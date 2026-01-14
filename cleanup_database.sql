
-- WordPress Database Cleanup SQL Commands
-- Run these in your WordPress database (usually via phpMyAdmin or similar)
-- BACKUP YOUR DATABASE FIRST!

-- 1. Remove orphaned postmeta (metadata for posts that no longer exist)
DELETE pm FROM wp_postmeta pm
LEFT JOIN wp_posts p ON pm.post_id = p.ID
WHERE p.ID IS NULL;

-- 2. Remove orphaned termmeta (metadata for terms that no longer exist)
DELETE tm FROM wp_termmeta tm
LEFT JOIN wp_terms t ON tm.term_id = t.term_id
WHERE t.term_id IS NULL;

-- 3. Remove orphaned term relationships (relationships for posts that no longer exist)
DELETE tr FROM wp_term_relationships tr
LEFT JOIN wp_posts p ON tr.object_id = p.ID
WHERE p.ID IS NULL;

-- 4. Remove orphaned term relationships (relationships for terms that no longer exist)
DELETE tr FROM wp_term_relationships tr
LEFT JOIN wp_term_taxonomy tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
WHERE tt.term_taxonomy_id IS NULL;

-- 5. Update term counts (recalculate category/tag counts)
UPDATE wp_term_taxonomy tt SET count = (
    SELECT COUNT(*) FROM wp_term_relationships tr 
    WHERE tr.term_taxonomy_id = tt.term_taxonomy_id
);

-- 6. Remove orphaned comments meta
DELETE cm FROM wp_commentmeta cm
LEFT JOIN wp_comments c ON cm.comment_id = c.comment_ID
WHERE c.comment_ID IS NULL;

-- 7. Remove orphaned user meta
DELETE um FROM wp_usermeta um
LEFT JOIN wp_users u ON um.user_id = u.ID
WHERE u.ID IS NULL;

-- 8. Remove auto-drafts older than 7 days
DELETE FROM wp_posts 
WHERE post_status = 'auto-draft' 
AND post_date < DATE_SUB(NOW(), INTERVAL 7 DAY);

-- 9. Remove orphaned attachment metadata
DELETE pm FROM wp_postmeta pm
LEFT JOIN wp_posts p ON pm.post_id = p.ID
WHERE pm.meta_key = '_wp_attachment_metadata' 
AND p.ID IS NULL;

-- 10. Optimize all tables (run one by one)
OPTIMIZE TABLE wp_posts;
OPTIMIZE TABLE wp_postmeta;
OPTIMIZE TABLE wp_terms;
OPTIMIZE TABLE wp_termmeta;
OPTIMIZE TABLE wp_term_taxonomy;
OPTIMIZE TABLE wp_term_relationships;
OPTIMIZE TABLE wp_comments;
OPTIMIZE TABLE wp_commentmeta;
OPTIMIZE TABLE wp_users;
OPTIMIZE TABLE wp_usermeta;
OPTIMIZE TABLE wp_options;

-- WooCommerce specific cleanup
-- 11. Remove orphaned order items
DELETE oi FROM wp_woocommerce_order_items oi
LEFT JOIN wp_posts p ON oi.order_id = p.ID
WHERE p.ID IS NULL;

-- 12. Remove orphaned order item meta
DELETE oim FROM wp_woocommerce_order_itemmeta oim
LEFT JOIN wp_woocommerce_order_items oi ON oim.order_item_id = oi.order_item_id
WHERE oi.order_item_id IS NULL;

-- 13. Check for orphaned data (counts only - run these to see how much orphaned data exists)
SELECT 'Orphaned postmeta' as type, COUNT(*) as count FROM wp_postmeta pm
LEFT JOIN wp_posts p ON pm.post_id = p.ID WHERE p.ID IS NULL
UNION ALL
SELECT 'Orphaned termmeta' as type, COUNT(*) as count FROM wp_termmeta tm
LEFT JOIN wp_terms t ON tm.term_id = t.term_id WHERE t.term_id IS NULL
UNION ALL
SELECT 'Orphaned term relationships' as type, COUNT(*) as count FROM wp_term_relationships tr
LEFT JOIN wp_posts p ON tr.object_id = p.ID WHERE p.ID IS NULL;
