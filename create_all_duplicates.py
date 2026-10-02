"""Create duplicates for every product returned by the replacements endpoint."""

import argparse
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

from config import WORDPRESS_URL
from createduplicates import duplicate_product


_BASE_DIR = Path(__file__).resolve().parent
REPLACEMENTS_ENDPOINT = (
    f"{WORDPRESS_URL.rstrip('/')}/wp-json/custom/v1/products-with-replacements"
)
DEFAULT_PER_PAGE = 100
REQUEST_TIMEOUT = 30
REQUEST_RETRIES = 3
START_LOG_PATTERN = re.compile(
    r"\[(?P<sequence>\d+)\] Creating duplicate for product id=(?P<product_id>\d+)"
)
RUN_START_LOG_PATTERN = re.compile(r"Starting duplicate run:")
SUCCESS_LOG_PATTERN = re.compile(
    r"\[(?P<sequence>\d+)\] Duplicate created: new id=\d+"
)
FAILURE_LOG_PATTERN = re.compile(
    r"\[(?P<sequence>\d+)\] (?:Duplicate failed for product id=|"
    r"Unexpected error duplicating product id=)"
)


def configure_logging(log_file: Path | None = None) -> logging.Logger:
    """Configure the batch logger for both the console and a log file."""
    logger = logging.getLogger("create_all_duplicates")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = _BASE_DIR / f"create_all_duplicates_{timestamp}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.info("Logging to %s", log_file)
    return logger


def load_resume_state(
    log_file: Path, logger: logging.Logger
) -> tuple[set[int], set[int]]:
    """Return confirmed successes and ambiguous in-progress source product IDs."""
    started_by_sequence = {}
    successful_ids = set()
    pending_ids = {}
    run_number = 0

    with log_file.open("r", encoding="utf-8") as previous_log:
        for line in previous_log:
            if RUN_START_LOG_PATTERN.search(line):
                run_number += 1
                continue

            start_match = START_LOG_PATTERN.search(line)
            if start_match:
                sequence = start_match.group("sequence")
                product_id = int(start_match.group("product_id"))
                run_sequence = (run_number, sequence)
                started_by_sequence[run_sequence] = product_id
                pending_ids[run_sequence] = product_id
                continue

            success_match = SUCCESS_LOG_PATTERN.search(line)
            if success_match:
                run_sequence = (run_number, success_match.group("sequence"))
                product_id = started_by_sequence.get(run_sequence)
                if product_id is not None:
                    successful_ids.add(product_id)
                    pending_ids.pop(run_sequence, None)
                else:
                    logger.warning(
                        "Could not associate a success record with a source product "
                        "in %s: %s",
                        log_file,
                        line.strip(),
                    )
                continue

            failure_match = FAILURE_LOG_PATTERN.search(line)
            if failure_match:
                run_sequence = (run_number, failure_match.group("sequence"))
                pending_ids.pop(run_sequence, None)

    ambiguous_ids = set(pending_ids.values()) - successful_ids
    logger.info(
        "Resume log %s contains %d confirmed successes and %d ambiguous in-progress IDs",
        log_file,
        len(successful_ids),
        len(ambiguous_ids),
    )
    return successful_ids, ambiguous_ids


def fetch_replacement_page(
    session: requests.Session,
    page: int,
    per_page: int,
    logger: logging.Logger,
) -> dict:
    """Fetch and validate one page from the custom replacements endpoint."""
    params = {"per_page": per_page, "page": page}
    last_error = None

    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            response = session.get(
                REPLACEMENTS_ENDPOINT,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
            products = payload.get("products")
            total_pages = payload.get("pages")
            total_products = payload.get("total")

            if not isinstance(products, list):
                raise ValueError("response field 'products' is not a list")
            if not isinstance(total_pages, int) or total_pages < 1:
                raise ValueError("response field 'pages' is invalid")
            if not isinstance(total_products, int) or total_products < 0:
                raise ValueError("response field 'total' is invalid")

            logger.info(
                "Fetched page %d/%d: %d products (reported total: %d)",
                page,
                total_pages,
                len(products),
                total_products,
            )
            return payload
        except (requests.RequestException, ValueError, TypeError) as error:
            last_error = error
            logger.warning(
                "Could not fetch page %d, attempt %d/%d: %s",
                page,
                attempt,
                REQUEST_RETRIES,
                error,
            )
            if attempt < REQUEST_RETRIES:
                time.sleep(attempt)

    raise RuntimeError(f"Failed to fetch page {page}: {last_error}") from last_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create WooCommerce duplicates for all replacement products."
    )
    parser.add_argument(
        "--per-page",
        type=int,
        default=DEFAULT_PER_PAGE,
        help=f"Products requested per endpoint page (default: {DEFAULT_PER_PAGE}).",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="First endpoint page to process (default: 1).",
    )
    parser.add_argument(
        "--end-page",
        type=int,
        help="Last endpoint page to process; defaults to the endpoint's final page.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Stop after this many products; useful for a controlled test run.",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0,
        help="Seconds to wait between product creations (default: 0).",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Log file path; defaults to a timestamped file in the script directory.",
    )
    parser.add_argument(
        "--resume-from-log",
        type=Path,
        help=(
            "Skip source product IDs with confirmed success records in this previous "
            "batch log; failed and unrecorded products will be attempted again."
        ),
    )
    parser.add_argument(
        "--retry-incomplete",
        action="store_true",
        help=(
            "Retry IDs left at 'Creating duplicate' with no logged result. Use only "
            "after checking whether those requests created products."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and report eligible products without creating duplicates.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = configure_logging(args.log_file)

    if args.per_page < 1 or args.per_page > 100:
        logger.error("--per-page must be between 1 and 100")
        return 2
    if args.start_page < 1:
        logger.error("--start-page must be at least 1")
        return 2
    if args.end_page is not None and args.end_page < args.start_page:
        logger.error("--end-page must not be less than --start-page")
        return 2
    if args.limit is not None and args.limit < 1:
        logger.error("--limit must be at least 1")
        return 2
    if args.pause < 0:
        logger.error("--pause cannot be negative")
        return 2

    session = requests.Session()
    attempted = 0
    succeeded = 0
    failed = 0
    skipped = 0
    skipped_ambiguous = 0
    failed_products = []

    try:
        logger.info("Replacement endpoint: %s", REPLACEMENTS_ENDPOINT)
        mode = "DRY RUN (no products will be created)" if args.dry_run else "LIVE"
        logger.info("Mode: %s", mode)
        resume_success_ids, resume_ambiguous_ids = (
            load_resume_state(args.resume_from_log, logger)
            if args.resume_from_log
            else (set(), set())
        )
        first_page = fetch_replacement_page(
            session, args.start_page, args.per_page, logger
        )
        total_pages = first_page["pages"]
        last_page = args.end_page or total_pages
        if last_page > total_pages:
            logger.warning(
                "Requested end page %d exceeds endpoint total %d; using %d",
                last_page,
                total_pages,
                total_pages,
            )
            last_page = total_pages

        logger.info(
            "Collecting products from pages %d-%d of %d before creation; per_page=%d",
            args.start_page,
            last_page,
            total_pages,
            args.per_page,
        )

        products_to_process = []
        seen_product_ids = set()
        repeated_endpoint_items = 0
        for page in range(args.start_page, last_page + 1):
            payload = (
                first_page
                if page == args.start_page
                else fetch_replacement_page(session, page, args.per_page, logger)
            )

            for product in payload["products"]:
                product_id = product.get("id")
                if isinstance(product_id, int):
                    if product_id in seen_product_ids:
                        repeated_endpoint_items += 1
                        continue
                    seen_product_ids.add(product_id)
                products_to_process.append(product)

        logger.info(
            "Collected %d unique products; ignored %d repeated endpoint entries",
            len(products_to_process),
            repeated_endpoint_items,
        )

        for product in products_to_process:
            product_id = product.get("id")
            source_sku = product.get("sku", "")

            if isinstance(product_id, int) and product_id in resume_success_ids:
                skipped += 1
                logger.info(
                    "Skipping confirmed success from resume log: id=%d sku=%s",
                    product_id,
                    source_sku,
                )
                continue

            if (
                isinstance(product_id, int)
                and product_id in resume_ambiguous_ids
                and not args.retry_incomplete
            ):
                skipped_ambiguous += 1
                logger.warning(
                    "Skipping ambiguous in-progress ID=%d sku=%s; inspect the site "
                    "or rerun with --retry-incomplete",
                    product_id,
                    source_sku,
                )
                continue

            if args.limit is not None and attempted >= args.limit:
                logger.info("Reached requested limit of %d products", args.limit)
                break

            replacement_sku = product.get("replacement_sku", "")
            attempted += 1

            if not isinstance(product_id, int):
                failed += 1
                failed_products.append((product_id, source_sku, "invalid id"))
                logger.error(
                    "[%d] Skipping product with invalid id=%r, sku=%s",
                    attempted,
                    product_id,
                    source_sku,
                )
                continue

            if args.dry_run:
                logger.info(
                    "[DRY RUN %d] Would duplicate source id=%d sku=%s replacement_sku=%s",
                    attempted,
                    product_id,
                    source_sku,
                    replacement_sku,
                )
                continue

            logger.info(
                "[%d] Creating duplicate for product id=%d sku=%s replacement_sku=%s",
                attempted,
                product_id,
                source_sku,
                replacement_sku,
            )
            try:
                new_product = duplicate_product(product_id)
            except Exception:
                failed += 1
                failed_products.append((product_id, source_sku, "exception"))
                logger.exception(
                    "[%d] Unexpected error duplicating product id=%d",
                    attempted,
                    product_id,
                )
            else:
                if new_product is None:
                    failed += 1
                    failed_products.append((product_id, source_sku, "API failure"))
                    logger.error(
                        "[%d] Duplicate failed for product id=%d sku=%s",
                        attempted,
                        product_id,
                        source_sku,
                    )
                else:
                    succeeded += 1
                    logger.info(
                        "[%d] Duplicate created: new id=%s sku=%s",
                        attempted,
                        new_product.get("id"),
                        new_product.get("sku"),
                    )

            if args.pause:
                time.sleep(args.pause)

    except KeyboardInterrupt:
        logger.warning(
            "Interrupted by user. Resume with this log; inspect any ID logged as "
            "Creating duplicate without a later result before using --retry-incomplete."
        )
        return 130
    except Exception:
        logger.exception("Batch stopped before completion")
        return 1
    finally:
        session.close()

    logger.info(
        "Run complete: attempted=%d succeeded=%d failed=%d "
        "skipped_from_resume_log=%d skipped_ambiguous=%d",
        attempted,
        succeeded,
        failed,
        skipped,
        skipped_ambiguous,
    )
    if failed_products:
        logger.error("Failed products: %s", failed_products)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())