/* Helper functions
----*/

	var isRTL = jQuery("html").attr("dir") === "rtl" ? true : false;

	class XTouchSwipe {

	  constructor(el) {
		this.touchStaX;
		this.toucnendX; // touch position
		this.touchSta;
		this.touchEnd;  // touch time

		el = el || document.body;
		if (el.getAttribute('x-swipe') === null) {
		  el.setAttribute('x-swipe', '');
		  el.addEventListener('touchstart', this.setTouchSta.bind(this));
		  el.addEventListener('mousedown', this.setTouchSta.bind(this));
		  el.addEventListener('touchend', this.setTouchEnd.bind(this));
		  el.addEventListener('mouseup', this.setTouchEnd.bind(this));
		}
	  }

	  handleGesture() {
		if (Math.abs(this.touchEndX - this.touchStaX) < 80) return; // min 80px distance
		if ((this.touchEnd - this.touchSta) > 500) return;          // max 500ms dragging

		const direction = this.touchEndX < this.touchStaX ? 'left' : 'right';
		const event = new CustomEvent('x-swipe', { bubbles: true, detail: direction });
		document.body.dispatchEvent(event);
	  }

	  setTouchSta(e) {
		this.touchStaX = e.type === 'touchstart' ? e.changedTouches[0].screenX : e.screenX;
		this.touchSta = new Date().getTime();
	  }

	  setTouchEnd(e) {
		this.touchEndX = e.type === 'touchend' ? e.changedTouches[0].screenX : e.screenX;
		this.touchEnd = new Date().getTime();
		this.handleGesture();
	  }

	}

	function debounce(callback, wait) {
	  let timeout;
	  return (...args) => {
	      clearTimeout(timeout);
	      timeout = setTimeout(function () { callback.apply(this, args); }, wait);
	  };
	}

	function stringContainsArrayValue(inputString, array) {
	  // Convert the input string to lowercase for case-insensitive comparison
	  const lowerInputString = inputString.toLowerCase();

	  // Check if any lowercase array value is present in the lowercase input string
	  return array.some(value => lowerInputString.includes(value.toLowerCase()));
	}

	function getParams() {

        var url = decodeURIComponent(window.location.href);
            url = url.split('?');

        var query = url[1];
        var params = new Object;

        if (typeof(query) != 'undefined' && query != null) {
            var vars = query.split('&');
            for (var i = 0; i < vars.length; i++) {
                var pair = vars[i].split('=');
                params[pair[0]] = decodeURIComponent(pair[1]);
            }
            return (jQuery.isEmptyObject(params)) ? false : params;
        }

        return false;
    }

    function clearParams(shopURL) {

        var url = shopURL;
            url = url.split('?');

        var query = url[1];
        var params = '';
        var newshopURL = url[0];

        if (typeof(query) != 'undefined' && query != null) {
            var vars = query.split('&');
            for (var i = 0; i < vars.length; i++) {
                var pair = vars[i].split('=');
                if (vehicleParams && !vehicleParams.includes(pair[0])) {
                    params += '&'+pair[0]+'='+pair[1];
                }
            }

            if (params.length && params.includes('&')) {newshopURL += '?'+params;}

            return newshopURL;
        }

        return false;
    }

    function createURL(shopURL,data,reload = true){

        var newshopURL = clearParams(shopURL);

        if (newshopURL) {
            shopURL = newshopURL;
        }

        if (shopURL.indexOf("?") == -1){
            shopURL += '?';
        }

        jQuery.each(data, function(key, value) {
            if (value.length) {
                if (key == 'year') {key = 'yr';}
                shopURL += '&'+key+'='+value;
            }
        });

        shopURL = shopURL.replace('?&', '?');

        shopURL = encodeURI(shopURL);

        if (reload) {
            window.location.assign(shopURL);
        } else {
            history.pushState({}, null, shopURL);
        }

    }

    function unique(array){
		return array.filter(function (value, index, self) {
	        return self.indexOf(value) === index;
	    });
	}

    function uniqueID() {return Math.floor((Math.random() * 1000000) + 1);}


	function isInArray(value, array) {return array.indexOf(value) > -1;}

	jQuery.fn.inView = function(win,observe,offset=0) {

        var observe  = (observe) ? observe : 0.6,
            win      = (win) ? win : window,
        	height 	 = jQuery(this).outerHeight(),
            scrolled = jQuery(win).scrollTop() - offset,
            viewed   = scrolled + jQuery(win).height(),
            top 	 = jQuery(this).offset().top,
            bottom   = top + height;
        return (top + height * observe) <= viewed && (bottom - height * observe) >= scrolled;
        
    };

    function toggleBack(element,toggle){

        var $this  = jQuery(element),
            isOpen = false;

		var	addToCart = jQuery('.single_variation_wrap').length ? jQuery('.single_variation_wrap') : jQuery('form.cart:not(.variations_form)');


        toggle.unbind('click').on('click',function(){

            toggle.toggleClass('active');

            if (jQuery(window).width() < 1263) {
            	if (!toggle.parents('.footer').length) {
            		jQuery('.sticky-dashboard').toggleClass('active');
            	}
            	if (addToCart.length) {
		            addToCart.toggleClass('transform');
		        }
            }

            jQuery(window).on('resize',function(){
				if (jQuery(window).width() < 1263) {
					if (jQuery('.hbe-toggle.active').length) {
	            		jQuery('.sticky-dashboard').toggleClass('active');
					}
	            	if (addToCart.length) {
			            addToCart.toggleClass('transform');
			        }
	            }
	        });

            if (isOpen==false) {
                isOpen=true;
            } else {
                isOpen=false;
            }

            if (toggle.hasClass('active')) {

				jQuery('.header .hbe-toggle.active').not(toggle).not('.mobile-toggle').not('.off-toggle').each(function(){
					jQuery(this).trigger('click');
				});
				jQuery('.footer .hbe-toggle.active').not(toggle).not('.mobile-toggle').not('.off-toggle').each(function(){
					jQuery(this).trigger('click');
				});
				jQuery('.submenu-toggle-click.mm-true.active').each(function(){
					jQuery(this).trigger('click');
				});
			}

        });

        
    }

    function isolate($link){
		if ($link.next('ul').length != 0) {
            if ($link.parent().hasClass('isolate')) {
				$link.parent().removeClass('isolate').removeClass('disable');
				if ($link.closest('.isolate').length) {
                	$link.closest('.isolate').removeClass('disable').find('.hide').removeClass('hide');
                } else {
                	$link.parents('.mobile-menu').find('.hide').removeClass('hide');
                }
			} else {
                $link.parent().addClass('isolate');
                $link.parents('.mobile-menu').find('.isolate').not($link.parent()).addClass('disable');
                $link.parent().siblings().addClass('hide');
            }
        };
	}

/* Lazy loading
----*/

	function lazyLoad(container){

		if (container != null) {

			let lazyImages = [].slice.call(container.querySelectorAll("img.lazy"));
			let lazyVideos = [].slice.call(container.querySelectorAll("video.lazy"));

			if ("IntersectionObserver" in window) {

				// Images

					let lazyImageObserver = new IntersectionObserver(function(entries, observer) {
						entries.forEach(function(entry) {
							if (entry.isIntersecting) {
								let lazyImage = entry.target;
								lazyImage.src = lazyImage.dataset.src;

								if (lazyImage.classList.contains('single') && window.innerWidth < 768) {
									let respImg = lazyImage.getAttribute('data-img-resp');
									respImg = respImg.split('|');
									lazyImage.src = respImg[0];
									lazyImage.setAttribute('width',respImg[1]);
									lazyImage.setAttribute('height',respImg[2]);
								}

								lazyImage.onload = function() {
								    lazyImage.classList.remove("lazy");
								    lazyImage.parentElement.classList.add("loaded");
								    lazyImageObserver.unobserve(lazyImage);
								};
								
							}
						});
					});

					lazyImages.forEach(function(lazyImage) {
						lazyImageObserver.observe(lazyImage);
					});

				// Videos

					let lazyVideoObserver = new IntersectionObserver(function(entries, observer) {
						entries.forEach(function(video) {
							if (video.isIntersecting) {

								for (var source in video.target.children) {
									var videoSource = video.target.children[source];
									if (typeof videoSource.tagName === "string" && videoSource.tagName === "SOURCE") {
										videoSource.src = videoSource.dataset.src;
									}
								}

								video.target.load();
								video.target.classList.remove("lazy");
								lazyVideoObserver.unobserve(video.target);
							}
						});
					});

					lazyVideos.forEach(function(lazyVideo) {
						lazyVideoObserver.observe(lazyVideo);
					});

			} else {

				let active = false;

				const lazyLoad = function() {
					if (active === false) {

					  	active = true;

						setTimeout(function() {

							lazyImages.forEach(function(lazyImage) {

								if ((lazyImage.getBoundingClientRect().top <= window.innerHeight && lazyImage.getBoundingClientRect().bottom >= 0) && getComputedStyle(lazyImage).display !== "none") {

									lazyImage.src = lazyImage.dataset.src;

									lazyImage.onload = function() {
									    lazyImage.classList.remove("lazy");
									    lazyImage.parentElement.classList.add("loaded");
									    lazyImages = lazyImages.filter(function(image) {
											return image !== lazyImage;
										});
									};

									if (lazyImages.length === 0) {
										document.removeEventListener("scroll", lazyLoad);
										window.removeEventListener("resize", lazyLoad);
										window.removeEventListener("orientationchange", lazyLoad);
									}
								}
							});

							lazyVideos.forEach(function(lazyVideo) {

								if ((lazyVideo.getBoundingClientRect().top <= window.innerHeight && lazyVideo.getBoundingClientRect().bottom >= 0) && getComputedStyle(lazyVideo).display !== "none") {

									for (var source in lazyVideo.children) {
										var videoSource = lazyVideo.children[source];
										if (typeof videoSource.tagName === "string" && videoSource.tagName === "SOURCE") {
											videoSource.src = videoSource.dataset.src;
										}
									}

									if (lazyVideos.length === 0) {
										document.removeEventListener("scroll", lazyLoad);
										window.removeEventListener("resize", lazyLoad);
										window.removeEventListener("orientationchange", lazyLoad);
									}
								}
							});

							active = false;

						}, 200);
					}
				};

				document.addEventListener("scroll", lazyLoad);
				window.addEventListener("resize", lazyLoad);
				window.addEventListener("orientationchange", lazyLoad);

			}

		}

	}

	document.addEventListener("DOMContentLoaded", lazyLoad(document));
	document.addEventListener("DOMContentLoaded", function(){
		var video = document.querySelector('.ftr-video');
		if (typeof(video) != 'undefined' && video != null) {video.play();}
		var videos = document.querySelectorAll('.video-container');
		if (typeof(videos) != 'undefined' && videos != null) {
			videos.forEach(function(item){
				item.play();
			})
		}
	});

	function changeSinglePostImage(){
		let lazyImage = document.querySelector('.image-container-single.loaded .single');
		if (lazyImage) {
			if (window.innerWidth > 768) {
				let respImg = lazyImage.getAttribute('data-img-desk');
				respImg = respImg.split('|');
				lazyImage.src = respImg[0];
				lazyImage.setAttribute('width',respImg[1]);
				lazyImage.setAttribute('height',respImg[2]);
			} else {
				let respImg = lazyImage.getAttribute('data-img-resp');
				respImg = respImg.split('|');
				lazyImage.src = respImg[0];
				lazyImage.setAttribute('width',respImg[1]);
				lazyImage.setAttribute('height',respImg[2]);
			}
		}
	}
	window.onresize = changeSinglePostImage;

/* Gsap lightbox
----*/

	function lightImage(src,overlay){

		if (
			src.includes('.jpg') ||
			src.includes('.jpeg') ||
			src.includes('.png') ||
			src.includes('.bmp') ||
			src.includes('.gif') ||
			src.includes('.svg')
		) {
			
			var img = document.createElement('img');
			img.src = src;

			var loaded = false;

			img.onload = function() {

				if (loaded) {
                    return;
                }

				if (overlay.find('img').length == 0) {
					overlay.prepend(img);
				}

				loaded = true;
			}
			
		} else if (src.includes('youtu') || src.includes('vimeo')) {
			var iframe = document.createElement('iframe');

			src = src.replace('watch?v=', 'embed/');
            src = src.replace('//vimeo.com/', '//player.vimeo.com/video/');
            src = (src.indexOf("?") == -1) ? src += '?' : src += '&';

			iframe.src = src+'autoplay=1';
			iframe.frameborder = '0';
			iframe.width  = '1280';
			iframe.height = '720';
			iframe.allow  = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
			iframe.allowfullscreen = true;
			overlay.prepend(iframe);
		} else if (src.includes('mp4') || src.includes('webm') || src.includes('ogv')) {
			var video = document.createElement('video');
			video.src = src;
			video.autoplay = true;
			video.controls = true;
			overlay.prepend(video);
		}
	}

	function gsapLightbox(element,gallery){

		var href = element.attr('href');

	  	if (
			href.includes('.jpg') ||
			href.includes('.jpeg') ||
			href.includes('.png') ||
			href.includes('.bmp') ||
			href.includes('.gif') ||
			href.includes('.svg') ||
			href.includes('youtu') ||
			href.includes('mp4') ||
			href.includes('webm') ||
			href.includes('webp') ||
			href.includes('ogv')
		){

			if (!jQuery('.gsap-lightbox-overlay').length) {

				var structure = (gallery == true) ? 
				jQuery('<div class="gsap-lightbox-overlay"><div class="image-wrapper"></div><a href="#" class="gsap-lightbox-controls gsap-lightbox-toggle"></a><a href="#" class="gsap-lightbox-controls gsap-lightbox-nav prev" data-direction="prev"></a><a href="#" class="gsap-lightbox-controls gsap-lightbox-nav next" data-direction="next"></a><svg class="placeholder" viewBox="0 0 20 4"><circle cx="2" cy="2" r="2" /><circle cx="10" cy="2" r="2" /><circle cx="18" cy="2" r="2" /></svg></div>') :
				jQuery('<div class="gsap-lightbox-overlay"><div class="image-wrapper"></div><a href="#" class="gsap-lightbox-controls gsap-lightbox-toggle"></a><svg class="placeholder" viewBox="0 0 20 4"><circle cx="2" cy="2" r="2" /><circle cx="10" cy="2" r="2" /><circle cx="18" cy="2" r="2" /></svg></div>');

				jQuery('body').append(structure);

				var overlay = jQuery('.gsap-lightbox-overlay'),
					wrapper = overlay.find('.image-wrapper'),
					toggle  = overlay.find('.gsap-lightbox-toggle'),
					loading = overlay.find('.gsap-lightbox-toggle');

				var tl = new gsap.timeline({paused: true});

				tl.from(toggle,0.2, {
				  opacity:0,
				  ease:"expo.out"
			  	},'+=0.2');

				tl.from(toggle,1.2, {
				  x:'-12px',
				  ease:"elastic.out(1, 0.5)"
			  	},'-=0.2');



				if (gallery == true) {

					var nav  	    = overlay.find('.gsap-lightbox-nav'),
						next        = overlay.find('.next'),
						prev        = overlay.find('.prev'),
						gallerySet  = [],
						count       = 0,
						galleryName = element.data('gallery');

					tl.from(nav,0.2, {
						opacity:0,
					},'-=1.1');

					tl.from(prev,1.2, {
					  x:'-40px',
					  ease:"elastic.out(1, 0.5)"
				  	},'-=1.1');

				  	tl.from(next,1.2, {
					  x:'40px',
					  ease:"elastic.out(1, 0.5)"
				  	},'-=1.2');

					jQuery('a[data-gallery="'+galleryName+'"]').each(function(){
						gallerySet.push(jQuery(this).attr('href'));
					});

					if (!gallerySet.length) {
						jQuery('a').each(function(){
							gallerySet.push(jQuery(this).attr('href'));
						});
					}

					count = gallerySet.indexOf(element.attr('href'));

					var max = gallerySet.length;

					if (max == 1) {
						jQuery('.gsap-lightbox-overlay .gsap-lightbox-nav').remove();
					}
					
					nav.on('click',function(e){

						overlay.find('img').remove();

						e.preventDefault();

						count += (jQuery(this).data('direction') == "next") ? 1 : -1;
						if (count < 0) {count = max - 1;}
						if (count >= max) {count = 0;}

						lightImage(gallerySet[count],wrapper);
					});

				}

				tl.add('active');

				tl.to(overlay,0.1, {
					opacity:0,
				});

				setTimeout(function(){
					overlay.addClass('active');
					tl.progress(0);
					tl.tweenTo('active');

					lightImage(element.attr('href'),wrapper);

				},50);

				toggle.on('click',function(e){
					e.preventDefault();
					tl.play();
					overlay.removeClass('active');
					setTimeout(function(){
						overlay.remove();
					},500);
				});

			}

		}
	}

/* Video trigger
----*/

	function videoTrigger(){
		jQuery('.video-btn').each(function(){

			var $this  = jQuery(this),
				video  = $this.parents('.post-video').find('.video-element'),
				image  = $this.parents('.post-video').find('.image-container'),
				embed  = (video.hasClass('iframevideo')) ? true : false,
				back   = $this.find('.back');

			$this.hover(
				function(){
					gsap.to(back,0.8, {
					  scale:1.1,
					  y:4,
					  ease:"elastic.out"
					});
				},
				function(){
					gsap.to(back,0.8, {
					  scale:1,
					  ease:"expo.out"
					});
				}
			);

			$this.unbind('click').on('click',function(e){
				e.preventDefault();

				if ($this.hasClass('video-modal')) {
					gsapLightbox($this,false);
				} else {

					if (jQuery(window).width() < 768) {

						src = $this.parents('.post-video').find('iframe').length ? $this.parents('.post-video').find('iframe').attr('src') : $this.parents('.post-video').find('video source').attr('data-src');
						
						$this.attr('href',src).addClass('video-modal');

						gsapLightbox($this,false);
					} else {
						setTimeout(function(){
							if (embed) {
								var src = video.attr('src');
								src =  (src.indexOf("?") == -1) ? src += '?' : src += '&';
								video.attr('src',src+'autoplay=1');
							} else {
								video.trigger('play');
							}
						},500);
					}
					
				}

				if (!$this.hasClass('video-modal')) {
					image.toggleClass('playing');
					video.toggleClass('playing');
					$this.parents('.post-video').find('.post-date-side').toggleClass('hidden');
				}

			});

		});
	}

	videoTrigger();

/* Product search
----*/

	(function($){

	    "use strict";

		const lang = $('html').attr('lang').split('-').shift();
		var productIndex = false;
		var noProductsFound = false

	    /* Fetch products data
		------------*/

			$.ajax({
				url: controller_opt.ajaxUrl,
	            type: 'GET',
	            data: {
	            	'action':'et__fetch_product_index',
	            },
	            success: function(response) {

	            	if (response) {

		            	response = JSON.parse(response);

	            		if (response['products']) {
	            			productIndex = response['products'];
	            		}

	            		if (response['no_products_found']) {
	            			noProductsFound = response['no_products_found'];
	            		}

            		}

	            	// console.log(response);

	            },
	            error: function(xhr, status, error) {
	                console.log(error);
	            }

		    });

	    function productSearch(form,query,currentQuery,element,category=""){

	        var search      = form.find('.search'),
	            inTag       = form.attr('data-tag'),
	            inAttr      = form.attr('data-attr'),
	            category    = form.find('select.category').val(),
	            sku         = form.attr('data-sku'),
	            description = form.attr('data-description'),
	            loading     = false;

	        form.find('.search-results').html('').removeClass('active');

	        query = query.trim();

	        search.parent().removeClass('loading');
	        form.find('.search-results').empty().removeClass('active');

	        if (query.length >= 3) {

	        	search.parent().addClass('loading');

	            form.find('.search-results').removeClass('empty');

	            search.parent().addClass('loading');
	            if (query != currentQuery) {

	            	if (productIndex) {

	            		var products = lang in productIndex ? productIndex[lang] : productIndex['default'];

	            		if (typeof category != "undefined" && category.length) {
							products = products.filter(product =>
							  Array.isArray(product.categories) &&
							  product.categories.some(cat => cat.slug === category)
							);
	            		}

	            		const searchInKeys = [
	            			'search_in_global'
	            		];

						if (searchInKeys.length) {

							let fuseKeys = [];
							let currency = controller_opt.currency;

							searchInKeys.forEach(function(item){
								fuseKeys.push({name: item, weight: 0.4});
							})

				        	const fuse = new Fuse(products, {
							    keys: fuseKeys,
							    threshold:parseFloat(controller_opt.threshold),
							    shouldSort:false,
								includeScore: true,
								ignoreLocation: true,
								useExtendedSearch: true,
							});

							products = fuse.search(String(query).trim());
							products = products.map(item => item.item);

							let pHTML = '';

							if (products.length) {
								for (let [index, product] of products.entries()) {

									let productClass = product['classes'];
									let output = '<li class="'+Object.values(productClass).join(' ')+'">';
										output += '<a href="'+product.link+'">';

										/* Image
										----------------*/

											let image = '';

											if (product.hasOwnProperty('image')) {

												let imageWidth  = parseFloat(product.image.width);
												let imageHeight = parseFloat(product.image.height);

			                					image += '<img ';

			                					
			                					image += 'src="'+product.image.url+'"';
												

			                					image += ' width="'+imageWidth+'" height="'+imageHeight+'" alt="'+product.image.alt+'" />';
												
											}

											if (image.length) {
												output += '<div class="product-image-wrapper"><div class="product-image">'+image+'</div></div>';
											}
										
										/* product-data
										----------------*/

											output += '<div class="product-data">';

												output += '<div class="product-categories">';

													if (product.hasOwnProperty('categories') && product.categories) {

														product.categories.forEach(function(entry){
															output += '<span>'+entry.name+'</span>';
														})

													}

													if (product.hasOwnProperty('sku') && product.sku) {
														output += '<span class="sku">'+controller_opt.SKU+' '+product.sku+'</span>';
													}

												output += '</div>';

												output += '<h3>'+product.title+'</h3>';
												
												let price = currency.length && 
												product.prices_by_currency && 
												product.prices_by_currency.hasOwnProperty(currency) ? 
												product.prices_by_currency[currency] : 
												product.price_html;

												output += '<div class="product-price">'+price+'</div>';

											output += '</div>';

										output += '</a></li>';

									/* Append Template
									----------------*/

										pHTML+=output;


								}
							} else if(noProductsFound) {
								pHTML = '<li class="no-results">'+noProductsFound+'</li>';
							}

							if (pHTML.length) {
								let output = '<ul class="product-list" id="product-search-results">';
                                	output += pHTML;
                                output += '</ul>';

                                form.find('.search-results').removeClass('active').addClass('active').html(output);
                                form.find('.search-wrapper').removeClass('loading');
                                
								lazyLoad(document.getElementById('product-search-results'));

							}

						}

	            	} else {

	            		let data = {
	            			action: 'search_product',
                        	keyword: query,
                        	category: category,
	            		}

	            		if (controller_opt.currency.length) {
	            			data['currency'] = controller_opt.currency
	            		}

	                	$.ajax({
	                        url:controller_opt.ajaxUrl,
	                        type: 'post',
	                        data: data,
	                        success: function(data) {

	                            currentQuery = query;
	                            search.parent().removeClass('loading');

	                            if (!form.find('.search-results').hasClass('empty')) {

	                                if (data.length) {

	                                	let output = '';

	                                    data = JSON.parse(data);

	                                    console.log(data);

	                                    if (typeof(data['products']) != 'undefined') {
	                                        output += '<ul class="product-list" id="product-search-results">';
	                                        	output += data['products'];
	                                        output += '</ul>';
	                                    } else if(typeof(data['not_found']) != 'undefined') {
	                                        output += '<ul><li class="no-results">'+data['not_found']+'</li></ul>';
	                                    }


	                                    form.find('.search-results').html(output).addClass('active');

	                                    if (form.find('.search-results .no-results').length) {
	                                    	form.find('.search-results').addClass('no-results');
	                                    } else {
	                                    	form.find('.search-results').removeClass('no-results');
	                                    }

	                                    query = query.split(' ');

	                                    for (var i = 0; i < query.length; i++) {
	                                    	form.find('.search-results').highlight(query[i]);
	                                    }

		                           		lazyLoad(document.getElementById('product-search-results'));

	                                }

	                            }

	                        }
	                    });

	                }
	            }
	        } else {

	            search.parent().removeClass('loading');
	            form.find('.search-results').empty().removeClass('active').addClass('empty');

	        }
	    }

	    function createSearchURL(shopURL,data,reload = true){

	        if (shopURL.indexOf("?") == -1){
	            shopURL += '?';
	        }

	        $.each(data, function(key, value) {
	            if (value.length) {
	                if (key == 'year') {key = 'yr';}
	                if (!shopURL.includes(key+'='+value)) {
	                	shopURL += '&'+key+'='+value;
	                }
	            }
	        });

	        shopURL = shopURL.replace('?&', '?');

	        shopURL = encodeURI(shopURL);

	        if (reload) {
	            window.location.assign(shopURL);
	        } else {
	            history.pushState({}, null, shopURL);
	            $('.reload-all-attribute').trigger('click');
	        }

	    }

	    // --- Mobile detection (coarse pointer or UA fallback) ---
		var isMobile = (window.matchMedia && window.matchMedia('(pointer: coarse)').matches)
		    || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

	    $('form[name="product-search"]').each(function () {

		  var element       = this,
		      form          = $(this),
		      search        = form.find('.search'),
		      category      = form.find('.category').val(''),
		      inCat         = form.attr('data-in-category'),
		      currentQuery  = '',
		      button        = form.find('input[type="submit"]');

		  var mouse_is_inside = false;

		  // --- Select2 init/destroy (DRY & idempotent) ---
		  function initSelect2() {
		    if ($(window).width() >= 1263) {
		      if (!category.data('select2')) {
		        category.select2({
		          dir: controller_opt.lang,
		          dropdownAutoWidth: true,
		          dropdownParent: category.parent()
		        });
		      }
		    } else if (category.data('select2')) {
		      category.select2('destroy');
		    }
		  }
		  initSelect2();
		  $(window).on('resize.ps', initSelect2);

		  // --- Category change ---
		  category.on('change.ps', function () {
		    currentQuery = '';
		    var query = search.val();
		    productSearch(form, query, currentQuery, element);
		    mouse_is_inside = true;

		    // Trim Select2 label text
		    var $label = $(this).parent().find('.select2-selection__rendered');
		    $label.text($label.text().trim());
		  });

		  // --- Clear previous search handlers to avoid duplicates, then bind per device ---
		  search.off('.ps');

		  if (isMobile) {
		    // ===== MOBILE: NO KEY LIMITATIONS, FIRE ON ANY VALUE CHANGE =====
		    var composing = false;

		    search
		      .on('compositionstart.ps', function () { composing = true; })
		      .on('compositionend.ps', function () {
		        composing = false;
		        var q = $(this).val();
		        productSearch(form, q, currentQuery, element);
		        mouse_is_inside = true;
		      })
		      .on('input.ps', function () {
		        if (composing) return;
		        var q = $(this).val();
		        productSearch(form, q, currentQuery, element);
		        mouse_is_inside = true;
		      })
		      .on('keydown.ps', function (e) {
		        // Prevent Enter submit and run immediately
		        if (e.key === 'Enter' || e.keyCode === 13) {
		          e.preventDefault();
		          var q = $(this).val();
		          productSearch(form, q, currentQuery, element);
		          mouse_is_inside = true;
		        }
		      });

		  } else {
		    // ===== DESKTOP: KEEP YOUR ORIGINAL KEY FILTERING =====
		    search.on('keyup.ps input.ps', function (e) {
		      const $input = $(this);
		      const key = e.keyCode;
		      const allowedKeys = [8, 32]; // Backspace and Space

		      // Skip if Ctrl+A or Ctrl+C or no input
		      if (
		        !$input.val() ||
		        ((e.ctrlKey || e.metaKey) && (key === 65 || key === 67))
		      ) {
		        return;
		      }

		      // Allow valid keys (A-Z, 0-9, numpad) or allowed special keys, or generic input event
		      if (
		        (key >= 65 && key <= 90) ||      // A-Z
		        (key >= 48 && key <= 57) ||      // 0-9 main keyboard
		        (key >= 96 && key <= 105) ||     // 0-9 numpad
		        allowedKeys.includes(key) ||
		        e.type === 'input'
		      ) {
		        var query = $input.val();
		        productSearch(form, query, currentQuery, element);
		        mouse_is_inside = true;
		      }

		      // Prevent Enter from triggering twice in embed
		      if (key === 13) {
		        e.preventDefault();
		      }
		    });
		  }

		  // --- Button click (unchanged) ---
		  button.on('click.ps', function (e) {
		    e.preventDefault();

		    var ajx       = ($('.widget_product_filter_widget').length && getParams() && typeof (getParams()['ajax']) != "undefined") ? true : false,
		        url       = ajx ? window.location.href : button.data('shop'),
		        reload    = ajx ? false : true,
		        activeCat = category.find('option:selected').val(),
		        searchVal = search.val(),
		        data      = {};

		    if (typeof (activeCat) != 'undefined' && activeCat.length) {
		      if (ajx) {
		        data['ca'] = activeCat;
		      } else {
		        data['product_cat'] = activeCat;
		      }
		    }

		    if (typeof (searchVal) != 'undefined' && searchVal.length) {
		      data['s'] = searchVal;
		      createSearchURL(url, data, reload);
		    }
		  });

		  // --- Click-away to close results (unchanged) ---
		  $(document).on('click.ps', function (e) {
		    const $target = $(e.target);

		    // Ignore clicks inside form[name="product-search"] or inside .search-results.active
		    if (
		      $target.closest('form[name="product-search"]').length ||
		      $target.closest('.search-results.active').length
		    ) {
		      return; // Do nothing
		    }

		    // Otherwise remove active class
		    $('.search-results.active').removeClass('active');
		    $('.et-product-search input[type="search"]').val('');
		  });

		});


	})(jQuery);

/* Social share
----*/

	(function($){

	    "use strict";

	    $('.social-share').on('click',function(){
	    	$(this).prev('.social-links').toggleClass('active');
	    });

	})(jQuery);

/* Sticky add to cart
----*/

	(function($) {

		"use strict";

		function stickyAddToCart(target, changeOn) {
			// Throttle scroll events
			let lastExecution = 0;
			const throttleDelay = 100; // Execute scrollPage at most every 100ms

			window.addEventListener('scroll', function() {
				const now = Date.now();
				if (now - lastExecution > throttleDelay) {
					scrollPage(target, changeOn);
					lastExecution = now;
				}
			}, false);
		}

		function scrollPage(target, changeOn) {
			var sy = (window.scrollY || document.documentElement.scrollTop);

			if (sy >= changeOn) {
				target.addClass('sticky');
				$('.et-mobile').addClass('up');
				$('.product-nav-tabs').addClass('up');
			} else {
				target.removeClass('sticky');
				$('.et-mobile').removeClass('up');
				$('.product-nav-tabs').removeClass('up');
			}
		}

		var addToCart = $('.single_variation_wrap').length ? $('.single_variation_wrap') : $('form.cart:not(.variations_form)');

		if ($(window).width() < 768 && addToCart.length) {
			// Calculate the offset
			var offset = $('.et-mobile.sticky-true').length
				? Math.round($('.et-mobile.sticky-true').outerHeight() + $('.product-nav-tabs').outerHeight())
				: $('.product-nav-tabs').outerHeight();

			// Add a placeholder to maintain layout stability
			$('<div class="add-to-cart-placeholder" style="height:' + addToCart.outerHeight() + 'px;"></div>').insertAfter(addToCart);

			// Initialize sticky behavior after delay to ensure elements are loaded
			setTimeout(function() {
				var changeOn = addToCart.offset().top + addToCart.outerHeight() - offset;
				if (changeOn) {
					stickyAddToCart(addToCart, changeOn);
				}
			}, 2000);
		}

	})(jQuery);

/* Product tab nav
----*/

	(function($){

	    "use strict";

	    function stickyNavTabs(navTabs,changeOn) {

	    	if( !didScroll ) {
                didScroll = true;
                scrollPage(navTabs,changeOn);
            }

	        window.addEventListener( 'scroll', function( event ) {
	            if( !didScroll ) {
	                didScroll = true;
	                scrollPage(navTabs,changeOn);
	            }
	        }, false );

	    }

	    function scrollPage(navTabs,changeOn) {
	        var sy = (window.pageYOffset || document.documentElement.scrollTop);

    		if ( sy >= changeOn ) {
        		$this
        		.addClass('active')
        		.css('top',$('.et-mobile').height());
        	} else {
        		$this
        		.removeClass('active');
        	}

	        didScroll = false;
	    }

	    if ($(window).width() < 768 && $('.product-nav-tabs').length) {

				var $this 	  = $('.product-nav-tabs');
				var offset 	  = $('.product-nav-tabs').outerHeight();
				var didScroll = false;
				var prefix    = 'product-nav-';
		        var changeOn  = $('.et-mobile.sticky-true').length ? $('.et-mobile.sticky-true').outerHeight() : 0;

				$('.product-nav-tabs li:first-child a').addClass('active');

			    $('<div class="nav-tabs-placeholder" style="height:'+$this.outerHeight()+'px;"></div>').insertAfter($this);

			    stickyNavTabs($this,changeOn);

			    $('.product-nav-tabs li a').each(function(){

		    		let thisTarget = $(this).attr('data-target');

		    		switch(thisTarget){
		    			case 'info':
		    				$('.summary-details > .et-accordion').attr('id',prefix+'target-info').addClass(prefix+'target');
		    			break;
		    			case 'fbt':
		    				$('.fbt-products').attr('id',prefix+'target-fbt').addClass(prefix+'target');
		    			break;
		    			case 'description':
		    				$('.before-description-wrap').attr('id',prefix+'target-description').addClass(prefix+'target');
		    			break;
		    			case 'vehicles':
		    				$('.single-product-vehicles').attr('id',prefix+'target-vehicles').addClass(prefix+'target');
		    			break;
		    			case 'compare':
		    				$('.compare-products').attr('id',prefix+'target-compare').addClass(prefix+'target');
		    			break;
		    			case 'reviews':
		    				$('.single-product-reviews-wrap').attr('id',prefix+'target-reviews').addClass(prefix+'target');
		    			break;
		    			case 'faq':
		    				$('.product-faq').attr('id',prefix+'target-faq').addClass(prefix+'target');
		    			break;
		    		}

		    	});

		    	function scrollToActive(){

		    		let activeOffset = $('.product-nav-tabs a.active').offset().left;

		    		if ($('.product-nav-tabs').width() < activeOffset) {

		    			gsap.to($('.product-nav-tabs'), {
				          scrollTo: {
				            x: activeOffset,
				            autoKill: false,
				          },
				          duration: 0.6
				        });

		    		} else if(activeOffset < 0) {
		        		gsap.to($('.product-nav-tabs'), {
				          scrollTo: {
				            x: 0,
				            autoKill: false,
				          },
				          duration: 0.6
				        });
		    		}
		    	}

		    	$('.product-nav-tabs').singlePageNav({
		            currentClass: 'active',
		            speed: 400,
		            easing: "swing",
		            offset:offset,
		            onComplete:scrollToActive
		        });

		    	$(window).on('scroll',scrollToActive);

		    	$('.single_add_to_cart_button').on('click',function(){
		    		if ($(this).hasClass('wc-variation-selection-needed')) {
			    		gsap.to(window, {
							duration: 1, 
							scrollTo: {y:$('table.variations'),offsetY:offset},
							ease:Power3.easeOut,
							onComplete:function(){

								var	addToCart = $('.single_variation_wrap').length ? $('.single_variation_wrap') : $('form.cart:not(.variations_form)');

								addToCart
				        		.removeClass('sticky');

				        		$('.footer-compare-icon').removeClass('hidden');
				        		$('.product > .post-social-share > .social-share').removeClass('hidden');
							}
						});
					}
		    	});

	    }

	})(jQuery);

/* GSAP config
----*/
	
	gsap.config({ nullTargetWarn:false});
	gsap.registerPlugin(ScrollToPlugin);

/* General
----*/

	(function($){

		"use strict";

		/* Post image replacement
		----*/


			function postImageReplace(){

				if ($(window).width() <= 767) {
					$('#single-post-page .image-container-single').attr('style','background-image:url('+$('#single-post-page .image-container-single img').attr('data-src'))+')';
					$('#single-post-page .image-container-single > svg').attr('viewBox','0 0 '+replaceWIDTH+' '+replaceHEIGHT);
					$('#single-post-page .image-container-single > svg > path').attr('d','M0,0H'+replaceWIDTH+'V'+replaceHEIGHT+'H0V0Z');
				} else {
					$('#single-post-page .image-container-single').removeAttr('style');
					$('#single-post-page .image-container-single > svg').attr('viewBox','0 0 '+originalWIDTH+' '+originalHEIGHT);
					$('#single-post-page .image-container-single > svg > path').attr('d','M0,0H'+originalWIDTH+'V'+originalHEIGHT+'H0V0Z');
				}

			}

			if (
				$('#single-post-page .image-container-single').length
			) {

				var originalWIDTH  = $('#single-post-page .image-container-single img').attr('width'),
					originalHEIGHT = $('#single-post-page .image-container-single img').attr('height');

				var replaceWIDTH  = 600,
					replaceHEIGHT = 400;

				postImageReplace();

				$(window).resize(postImageReplace);

			}

		/* WPML Language switcher
		----*/

			$('.no-ls a').on('click',function(){
				alert(controller_opt.noLanguage);
			});

			$('.widget_icl_lang_sel_widget .wpml-ls-current-language > a')
			.append('<span class="toggle"></span>');

			$('.wpml-ls-legacy-dropdown-click a > span.toggle').on('click',function(e){
				$(this).parent().toggleClass('active');
				if ($(this).parent().next('ul').length != 0) {
					$(this).parent().toggleClass('animate');
					$(this).parent().next('ul').stop().slideToggle(300);
				};
				e.preventDefault();
			});

			$('.wpml-ls-legacy-dropdown .wpml-ls-current-language').hover(
				function(){
					$(this).toggleClass('active');
					if ($(this).find('ul').length != 0) {
						$(this).toggleClass('animate');
						$(this).find('ul').stop().slideToggle(300);
					};
				},
				function(){
					$(this).toggleClass('active');
					if ($(this).find('ul').length != 0) {
						$(this).toggleClass('animate');
						$(this).find('ul').stop().slideToggle(300);
					};
				}
			);

		/* Currency switcher
		----*/

			if ($('#alg_currency_selector').length) {
				$('#alg_currency_selector a').on('click',function(){
					localStorage.setItem("currency", $(this).text());
				});
			}

		/* Widget navigation
		----*/

			$('.widget_nav_menu').each(function(){

				var $this = $(this);
				var childItems = $this.find('.menu-item-has-children > a')
				.append('<span class="toggle"></span>');

				if ($this.find('.menu-item-has-children > a').attr( "href" ) == "#") {
					$this.find('.menu-item-has-children > a').on('click',function(e){
						$(this).toggleClass('active');
						if ($(this).next('ul').length != 0) {
							$(this).toggleClass('animate');
							$(this).next('ul').stop().slideToggle(300);
						};
						e.preventDefault();
					});
				} else {
					$this.find('.menu-item-has-children > a > span.toggle').on('click',function(e){
						e.stopImmediatePropagation();
						$(this).toggleClass('active');
						if ($(this).parent().next('ul').length != 0) {
							$(this).parent().toggleClass('animate');
							$(this).parent().next('ul').stop().slideToggle(300);
						};
						e.preventDefault();
					});
				}

			});

			var activeParams = getParams();
			var categoryParam = false;

			$.each(activeParams,function(key,value){
				if (key == 'product_cat') {
					categoryParam = value;
				}
			})


			$('.widget_product_categories').each(function(){

				var $this = $(this);

				if ($this.find('.count').length != 0) {
					$this.find('a').each(function(){
						var $self = $(this);
						var countClone = $self.next('.count').clone();
						$self.next('.count').remove();
						$self.append(countClone);
					});
				}

				var childItems = $this.find('.cat-parent > a');

				if (categoryParam) {
					$this.find('a[href*="'+categoryParam+'"]').each(function(){
						var href = $(this).attr('href');
						href = href.split('/');
						href.pop();
						href = href.slice(-1);
						if (categoryParam == href) {$(this).parent().addClass('current-cat');}
					});
				}

				$this.find('.current-cat').parents('.cat-parent').addClass('animate').children('a').addClass('active');
				$this.find('.current-cat').parents('.cat-parent').children('a').addClass('animate').children('span.toggle').addClass('active');
				$this.find('.current-cat').parents('ul.children').stop().slideDown(300);

				if ($this.find('.cat-parent > a').attr( "href" ) == "#") {
					$this.find('.cat-parent > a').on('click',function(e){
						$(this).toggleClass('active');
						if ($(this).parent().next('.children').length != 0) {
							$(this).parent().toggleClass('animate');
							$(this).parent().next('.children').stop().slideToggle(300);
						};
						e.preventDefault();
					});
				} else {
					$this.find('.cat-parent > a > span.toggle').on('click',function(e){
						e.stopImmediatePropagation();
						$(this).toggleClass('active');
						if ($(this).parent().next('.children').length != 0) {
							$(this).parent().toggleClass('animate');
							$(this).parent().next('.children').stop().slideToggle(300);
						};
						e.preventDefault();
					});
				}


			});

		/* Widget calendar
		----*/

			$('.widget_calendar').each(function(){

				var $this = $(this);
				var caption = $this.find('caption');

				$this.find('.wp-calendar-nav-prev a').clone().addClass('prev').html('').appendTo(caption);
				$this.find('.wp-calendar-nav-next a').clone().addClass('next').html('').appendTo(caption);
				$this.find('.wp-calendar-nav').remove();

			});

			$('.wp-block-calendar').each(function(){

				var $this = $(this);
				var caption = $this.find('caption');

				$this.find('.wp-calendar-nav a').clone().addClass('prev').html('').appendTo(caption);
				$this.find('.wp-calendar-nav a').clone().addClass('next').html('').appendTo(caption);
				$this.find('.wp-calendar-nav').remove();

			});

		/* Widget product search
		----*/

			$('.widget_product_search').each(function(){
				$('<div class="search-icon"></div>').insertAfter($(this).find('input[type="submit"]'));
			});

		/* Move to top button
		----*/

			var didScroll = false,
				nav       = $('.bullets-container');
	
			function showOnScroll() {
				window.addEventListener( 'scroll', function( event ) {
				    if( !didScroll ) {
				        didScroll = true;
				        scrollPage(400);
				    }
				}, false );
			}

			function scrollPage(activateOn) {
				var sy = window.pageYOffset;
				if ( sy >= activateOn ) {
					nav.addClass('animate');
				} else {
					nav.removeClass('animate');
				}

				didScroll = false;
			}

			showOnScroll();

			// $('.to-top').on('click',function(){
			// 	gsap.to(window, {
			// 		duration: 1, 
			// 		scrollTo: {y:$('.to-top').attr('href')},
			// 		ease:Power3.easeOut 
			// 	});
			// 	return false;
			// });


			$('.write-review').on('click',function(){

				var review = $(this);
				var offset = ($('.et-desktop.sticky-true.active').length) ? $('.et-desktop.sticky-true.active').height() : Math.round($('.et-mobile.sticky-true.active').height() + $('.product-nav-tabs').outerHeight());

				gsap.to(window, {
					duration: 1, 
					scrollTo: {
						y:review.attr('href'),
						offsetY:offset
					},
					ease:Power3.easeOut,
				});
				return false;
			});

			$('.woocommerce-review-link').on('click',function(){

				var review = $(this);

				gsap.to(window, {
					duration: 1, 
					scrollTo: {y:review.attr('href')},
					ease:Power3.easeOut 
				});
				return false;
			});

		/* Form placeholder
		----*/

			$('.widget_login, .widget_reglog').each(function(){
				var $this = $(this);

				$this.find('label').each(function(){
					var labelText = $(this).text();
					$(this).next('input').attr('placeholder',labelText);
					$(this).remove();
				});

				$this.find('input[type="submit"]').on("click",function(event) {

					if (!$this.find('input[type="text"]').val() || !$this.find('input[type="password"]').val() ||
						$this.find('input[type="text"]').val() == $this.find('input[type="text"]').data('placeholder') ||
						$this.find('input[type="password"]').val() == $this.find('input[type="password"]').data('placeholder')) {
						event.preventDefault();
					}

				});
			});

		/* Responsive tables
		----*/

			function responsiveTable(){

				if ($(window).outerWidth() <= 767) {
					$('table:not(.cbt):not(.wp-calendar-table)').addClass('responsive');
					$('table:not(.cbt):not(.wp-calendar-table)').parent().addClass('overflow-x');
				} else {
					$('table:not(.cbt):not(.wp-calendar-table)').removeClass('responsive');
					$('table:not(.cbt):not(.wp-calendar-table)').parent().removeClass('overflow-x');
				}

			}
			responsiveTable();
			$(window).resize(responsiveTable);

			
			if ($('.single-product-vehicles input').length) {
				window.addEventListener('keyup', debounce( () => {
				    var query = $('.single-product-vehicles input').val();
				    if (query) {

				    	$('.single-product-vehicles table').addClass('active-search');

				    	query = query.split(' ');

				    	var rows = [];

				    	$('.single-product-vehicles table tr').each(function(){
				    		if (stringContainsArrayValue($(this).text(), query)) {
				    			$(this).addClass('show');
				    		} else {
				    			$(this).removeClass('show');
				    		}
				    	});


				    } else {
				    	$('.single-product-vehicles table').removeClass('active-search');
				    	$('.single-product-vehicles table tr').removeClass('show');
				    }
				},200));
			}

		/* Color swatches
		----*/

			$('.swatch-color').each(function(){
				if ($(this).css('background-color') === 'rgb(255, 255, 255)') {
				   $(this).addClass('white');
				}
			});
			
		/* Products ask
		----*/

			setTimeout(function(){
				$('.cart-contents').parent().addClass('loaded');
			},1000);


			$('.ask-toggle').on('click',function(e){
				e.preventDefault();
				$('.ask-form').addClass('active');
			});

			$('.ask-title').on('click',function(){
				$('.ask-toggle').trigger('click');
			});

			$('.ask-close').on('click',function(){
				$('.ask-form').removeClass('active');
			});

			$('.ask-after').on('click',function(){
				$('.ask-close').trigger('click');
			});

			var pTitle = $('.single-product .entry-summary .entry-title').text();
			var sku = $('.single-product .entry-summary .sku').text();

			if(typeof(sku) != 'undefined' && sku.length){
				pTitle += ' / '+sku;
			}

			if(typeof(pTitle) != 'undefined' && pTitle.length){
				$('.ask-form').find('input[name="product-name"]').val(pTitle);
			}

		/* Buy now
		----*/

			function updateBuyNowLink() {

				var data            = {};
			    var buyNowLink      = jQuery('.buy-now-button').attr('href');
				var productQuantity = jQuery('form.cart input[name="quantity"]').val();

				if(productQuantity >= 1) {
					data['quantity'] = productQuantity;
				}

		    	if (jQuery('input[name="variation_id"]').length) {

			        var variation_id = jQuery('input[name="variation_id"]').val();

			        if (variation_id.length && variation_id != '0') {
			        	data['variation_id'] = jQuery('input[name="variation_id"]').val();
			        }

		        }

		        if (!$.isEmptyObject(data)) {

			    	jQuery.each(data, function(key, value) {
			            if (value.length) {
			                buyNowLink += '&'+key+'='+value;
			            }
			        });

			    	window.location.assign(buyNowLink);
		        }

			}

			$(document).on('click','.buy-now-button',function(e){
				e.preventDefault();

				if (!$(this).prev('.single_add_to_cart_button').hasClass('disabled')) {
					updateBuyNowLink();
				}
			});

		/* Fbt
		----*/

			var fbt        = $('.fbt .product'),
				totalPrice = Number($('.fbt-info .total-price span').html());

			if (fbt.length) {
				// Toggle

				function updateMiniCart(productCount) {

					var cartContents = parseInt($('.cart-contents').html());

					$('.cart-contents').html(cartContents + productCount);

			        $.ajax({
			            type: 'GET',
			            url: controller_opt.ajaxUrl,
			            data: {
			                action: 'update_mini_cart_content',
			            },
			            success: function(response) {
			                // Update the mini cart content
			                $('.widget_shopping_cart_content').html(response);
			            }
			        });
			    }

				var currencySymbol = $('.fbt-info .total-price bdi').text().match(/^[^\d]+/)[0].trim()

				$('.fbt-item').on('click',function(){
					var $this = $(this),
						price = Number($this.data('price')),
						bdi   = parseFloat($('.fbt-info .total-price bdi').text().replace(/[^0-9.-]+/g,""));
	
					if(isNaN(bdi)){
						bdi = 0;
					}

					$this.toggleClass('chosen');
					if (!$this.hasClass('chosen')) {
						totalPrice = Math.abs(bdi - price);
					} else {
						totalPrice = Math.abs(bdi + price);
					}

					totalPrice = parseFloat(totalPrice);
					totalPrice = totalPrice.toFixed(2);

					$('.fbt-info .total-price bdi').html(currencySymbol+totalPrice);

				});

				// Add to cart
				$('.add_to_cart_all').on('click',function(e){

					var $this = $(this),
						thiisText = $this.text();
					e.preventDefault();

					var fbtActive = $('.loop-products.fbt .fbt-item.chosen');

					if (!$this.hasClass('added')) {
						if (fbtActive.length) {

							$this.parent().addClass('loading');

							var products = [];


							fbtActive.each(function(){
								products.push($(this).data('product'));
							});

							if (products.length) {

								$.ajax({
						            type: 'POST',
						            url: controller_opt.ajaxUrl,
						            data: {
						                action: 'add_to_cart_all',
						                products: JSON.stringify(products),
						            },
						            success: function(response) {

						                $this
						                .addClass('added')
						                .html(controller_opt.allAdded)
						                .parent()
						                .removeClass('loading');

						                updateMiniCart(products.length);

						                setTimeout(function(){
						                	$this
						                	.removeClass('added')
						                	.html(thiisText);
						                },5000);
						            }
						        });

					        }
						}
					}
				});
			}

		/* Compare
		----*/

			$('.compare-table-single').find('.woocommerce-button[href="'+window.location.href+'"]').on('click',function(e){
				e.preventDefault();

				gsap.to(window, {
					duration: 1, 
					scrollTo: {y:'#wrap'},
					ease:Power3.easeOut 
				});
				return false;

			});

		/* Comments responses
		----*/

			$('.see-responses').on('click',function(e){
				e.preventDefault();
				$(this).next('.responses').toggleClass('active');
				
			});

		/* Mobile account navigation
		----*/

			$('.dashboard-mobile-toggle').on('click',function(){
				if (!$('.my-account-nav-wrapper .woocommerce-MyAccount-navigation').html()) {
					let theClone = $('.woocommerce-MyAccount-navigation').clone();
					$('.my-account-nav-wrapper .woocommerce-MyAccount-navigation').append(theClone.html());
				}
				$('.my-account-nav-wrapper').addClass('active');
				$('.sticky-dashboard').removeClass('active');
			});

			$('body').on('click','.dashboard-mobile-toggle-off',function(){
				$('.my-account-nav-wrapper').removeClass('active');
				$('.sticky-dashboard').addClass('active');
			});

		/* Attribute search
		----*/

			$("body").on('keyup','input.attr-search',function(e){
		        var filter = $(this).val();
		        $(this).next('ul').find('li').each(function(){
		            if ($(this).find('a').attr('title').search(new RegExp(filter, "i")) < 0) {
		                $(this).hide(0);
		            } else {
		                $(this).show();
		            }
		        });
		    });

		    let catalogOffset = false;

		    if (window.location.href.indexOf("catalog/#shop_brands") > -1) {
		    	catalogOffset = '#shop_brands';
			} else if (window.location.href.indexOf("catalog/#shop_categories") > -1) {
		    	catalogOffset = '#shop_categories';
			} else if (window.location.href.indexOf("catalog/#shop_make") > -1) {
		    	catalogOffset = '#shop_make';
			}

			if (catalogOffset) {
				gsap.to(window, {
					duration: 1, 
					scrollTo: {y:($(catalogOffset).offset().top - $('.et-desktop').height())},
					ease:Power3.easeOut 
				});
			}
			
		/* remove vehicle cookie if no product found
		----*/

			if ($('.woocommerce-no-products-found').length){
				$.removeCookie('vehicle', { path: '/' });
		    }

		/* highlishgt current vehicle
		----*/

		    function compareJSONObjects(obj1, obj2) {
			    if (typeof obj1 !== 'object' || typeof obj2 !== 'object') {
			        return false;
			    }

			    const keys1 = Object.keys(obj1);
			    const keys2 = Object.keys(obj2);

			    if (keys1.length !== keys2.length) {
			        return false;
			    }

			    if (!keys1.every(key => keys2.includes(key))) {
			        return false;
			    }

			    return keys2.every(key => {
			        if (key === 'year') {
			            return compareYearValues(obj1[key], obj2[key]);
			        } else {
			            return obj1[key] === obj2[key];
			        }
			    });
			}

			function compareYearValues(value1, value2) {
			    var years = [];

			    if (value2.includes('-')) {
			        var period = value2.split('-');
			        for (var i = parseInt(period[0]); i <= parseInt(period[1]); i++) {
			            years.push(i.toString());
			        }
			    } else if (value2.includes(',')) {
			        var period = value2.split(',');
			        for (var i = 0; i < period.length; i++) {
			            years.push(period[i].toString());
			        }
			    } else {
			        years.push(value2.toString());
			    }

			    return years.includes(value1.toString());
			}

			if (typeof $.cookie('vehicle') !== 'undefined' && $('.single-product-vehicles table').length) {
			    var currentVehicle = JSON.parse($.cookie('vehicle'));
			    $('.single-product-vehicles tbody tr').each(function () {
			        var thisVehicle = JSON.parse($(this).attr('data-vehicle'));

			        if (compareJSONObjects(currentVehicle, thisVehicle)) {


			            var $this = $(this).addClass("highlight");
			            $this.parent().animate({
			                scrollTop: $this.offset().top - $this.parent().offset().top
			            }, 'slow');
			        }
			    });

			    // if (!$('.single-product-vehicles tbody tr.highlight').length && $('.single-product-wrapper').hasClass('uni-false')) {
			    //     $('.post-layout-single > .container').prepend('<div class="vehicle-mismatched">'+controller_opt.mismatched+' <span>'+Object.values(currentVehicle).join(' ')+'</span></div>')
			    // }
			}

		/* Block cart sticky
		----*/

			function stickyCartSummary($cartOrderSummary) {
			    if (!$cartOrderSummary.length) return;

			    let offsetTop, originalWidth, setY, $placeholder;
			    let initialized = false;
			    let $parent = $('.wc-block-components-sidebar');

			    function enableSticky() {
			        if (initialized) return;

			        offsetTop = $cartOrderSummary.offset().top;
			        originalWidth = $cartOrderSummary.outerWidth();
			        setY = gsap.quickSetter($cartOrderSummary[0], "y", "px");


			        // Create placeholder
			        $placeholder = $('<div class="sticky-wc-block-cart__sidebar-placeholder" style="height:'+$cartOrderSummary.outerHeight()+'px"></div>')
			        .insertAfter($cartOrderSummary);

			        $(window).on('scroll.stickyCartSummary', function () {
			            const scrollTop = $(window).scrollTop() + ($('.header.sticky-true.active').is(":visible") ? $('.header.sticky-true.active').outerHeight() : 0) + 36; 
			            const parentTop = $parent.offset().top;
			            const parentBottom = parentTop + $parent.outerHeight();
			            const $cartOrderSummaryHeight = $cartOrderSummary.outerHeight();
			            const maxTranslate = parentBottom - $cartOrderSummaryHeight - offsetTop - 16;

			            if (scrollTop >= offsetTop && scrollTop <= maxTranslate + offsetTop) {
			                if (!$cartOrderSummary.hasClass('scroll')) {
			                    $cartOrderSummary.css({ width: originalWidth + 'px' });
			                }
			                $cartOrderSummary.addClass('scroll');
			                setY(scrollTop - offsetTop);
			            } else if (scrollTop > maxTranslate + offsetTop) {
			                setY(maxTranslate); // stop at bottom
			            } else {
			                if ($cartOrderSummary.hasClass('scroll')) {
			                    $cartOrderSummary.removeClass('scroll');
			                    $cartOrderSummary.removeAttr('style');
			                }
			                setY(0);
			            }
			        });

			        initialized = true;
			    }

			    function disableSticky() {
			        $(window).off('scroll.stickyCartSummary');
			        if ($cartOrderSummary.hasClass('scroll')) {
			            $cartOrderSummary.removeClass('scroll');
			            $cartOrderSummary.removeAttr('style');
			        }
			        if ($placeholder) $placeholder.remove();
			        initialized = false;
			    }

			    function updateStickyState() {
			        if ($(window).outerWidth() >= 1024) {
			            enableSticky();
			        } else {
			            disableSticky();
			        }
			    }

			    // On resize, update original width and reset sticky state if necessary
			    function updateWidthOnResize() {
			        if (initialized) {
			            originalWidth = $cartOrderSummary.next('.wp-block-woocommerce-cart-order-summary-block-placeholder').outerWidth();
			            $cartOrderSummary.css({ width: originalWidth + 'px' });
			        }
			    }

			    updateStickyState();
			    $(window).on('resize.stickyCartSummary', function () {
			        updateStickyState();
			        updateWidthOnResize(); // Ensure width is updated on resize
			    });
			}

			setTimeout(function(){
				$('.wc-block-cart__sidebar').wrapInner('<div class="sticky-wc-block-cart__sidebar">');
				stickyCartSummary($('.sticky-wc-block-cart__sidebar'));
			},3000);

			function stickyCartTotals($cartOrderSummary) {
			    if (!$cartOrderSummary.length) return;

			    let offsetTop, originalWidth, setY, $placeholder;
			    let initialized = false;
			    let $parent = $('.cart-collaterals');

			    function enableSticky() {
			        if (initialized) return;

			        offsetTop     = $cartOrderSummary.offset().top;
			        originalWidth = $cartOrderSummary.outerWidth();
			        setY          = gsap.quickSetter($cartOrderSummary[0], 'y', 'px');

			        // Create placeholder
			        $placeholder = $('<div class="sticky-wc-block-cart__sidebar-placeholder" style="height:' +
			                         $cartOrderSummary.outerHeight() + 'px"></div>').insertAfter($cartOrderSummary);

			        $(window).on('scroll.stickyCartTotals', function () {
			            const scrollTop  = $(window).scrollTop() +
			                               ($('.header.sticky-true.active').is(':visible')
			                                 ? $('.header.sticky-true.active').outerHeight()
			                                 : 0) + 36;
			            const parentTop    = $parent.offset().top;
			            const parentBottom = parentTop + $parent.outerHeight();
			            const boxHeight    = $cartOrderSummary.outerHeight();
			            const maxTranslate = parentBottom - boxHeight - offsetTop;

			            if (scrollTop >= offsetTop && scrollTop <= maxTranslate + offsetTop) {
			                if (!$cartOrderSummary.hasClass('scroll')) {
			                    $cartOrderSummary.css({ width: originalWidth + 'px' });
			                }
			                $cartOrderSummary.addClass('scroll');
			                setY(scrollTop - offsetTop);
			            } else if (scrollTop > maxTranslate + offsetTop) {
			                setY(maxTranslate); // stop at bottom
			            } else {
			                if ($cartOrderSummary.hasClass('scroll')) {
			                    $cartOrderSummary.removeClass('scroll').removeAttr('style');
			                }
			                setY(0);
			            }
			        });

			        initialized = true;
			    }

			    function disableSticky() {
			        $(window).off('scroll.stickyCartTotals');
			        if ($cartOrderSummary.hasClass('scroll')) {
			            $cartOrderSummary.removeClass('scroll').removeAttr('style');
			        }
			        if ($placeholder) $placeholder.remove();
			        initialized = false;
			    }

			    function updateStickyState() {
			        if ($(window).outerWidth() >= 1280) {
			            enableSticky();
			        } else {
			            disableSticky();
			        }
			    }

			    function updateWidthOnResize() {
			        if (initialized) {
			            originalWidth = $cartOrderSummary
			                .next('.wp-block-woocommerce-cart-order-summary-block-placeholder')
			                .outerWidth();
			            $cartOrderSummary.css({ width: originalWidth + 'px' });
			        }
			    }

			    updateStickyState();
			    $(window).on('resize.stickyCartTotals', function () {
			        updateStickyState();
			        updateWidthOnResize();
			    });
			}

			/* initialise */
			stickyCartTotals($('.cart_totals'));

			$('body').on('click','.comp-counter span',function(e){
				let val = parseInt($(this).parents('.product').find('input').val());
	                val += $(this).hasClass('minus') ? - 1 : + 1;
	            
	            let max = parseFloat($(this).parents('.product').find('input').attr('max'));

	                if (val == 0 || val < 0) {val = 1} else
	                if (val > max) {val = 1}

	                if (!isNaN(val)) {
	                    $(this).parents('.product').find('input').val(val);
	                    $(this).parents('.product').find('.add_to_cart_button').attr('data-quantity',val);
	                }
			});

			const container = document.querySelector('.price_label');

			if(container != null){
				[...container.childNodes].forEach(node => {
				  if (node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== '') {
				    node.remove(); // or wrap/replace as needed
				  }
				});
			}


		/* Layut control
		----*/

			$(".layout-control div").on('click',function(){

		        var $this  = $(this),
		            layout = $this.attr('data-layout'),
		            data   = new Object;

		        if (!$this.hasClass('chosen')) {
		            $this.addClass('chosen').siblings().removeClass('chosen');
		            $('.product-layout')
		            .removeClass('grid')
		            .removeClass('list')
		            .removeClass('comp')
		            .addClass(layout)

		        }

		    });

	})(jQuery);

/* Swiper & Lightbox
----*/

	(function($){

		"use strict";

		$('.post-gallery .slides').each(function(){

			var $this  = $(this);
			var swiper = new Swiper('#'+$(this).parent().attr('id'), {
				slidesPerView: 1,
				navigation: {
				    nextEl: '#'+$this.parents('.swiper-container').find('.swiper-button-next').attr('id'),
				    prevEl: '#'+$this.parents('.swiper-container').find('.swiper-button-prev').attr('id'),
				}
			});

		});

		$('.gallery').each(function(){
			$(this).find('a').unbind('click').on('click',function(e){
				var href = $(this).attr('href');
			  	if (
					href.includes('.jpg') ||
					href.includes('.jpeg') ||
					href.includes('.png') ||
					href.includes('.bmp') ||
					href.includes('.gif') ||
					href.includes('.svg')
				){
					e.preventDefault();
					gsapLightbox($(this),true);
				}
			});
		});

	    $('.post-content a').each(function(){

	    	$(this).unbind('click').on('click',function(e){
					
		    	var $this = $(this),
		    		href  = $(this).attr('href');

			  	if (
					href.includes('.jpg') ||
					href.includes('.jpeg') ||
					href.includes('.png') ||
					href.includes('.bmp') ||
					href.includes('.gif') ||
					href.includes('.svg')
				){

					e.preventDefault();
					gsapLightbox($this,false);
				}

			});

	    	
	    });

	    if ($('.loop-categories').length) {

	    	var columns = 6;

			var swiper = new Swiper('.loop-categories-wrapper', {
				direction:'horizontal',
				loop: false,
				spaceBetween: 16,
				slidesPerView: columns,
				grabCursor: true,
				autoHeight: true,
				navigation: {
				    nextEl: '.loop-categories-next',
				    prevEl: '.loop-categories-prev',
				},
				breakpoints: {
					200: {
						slidesPerView: 2,
						spaceBetween: 8,
					},
					375: {
						slidesPerView: 2,
						spaceBetween: 8,
					},
					425: {
						slidesPerView: 3,
						spaceBetween: 8,
					},
					768: {
						slidesPerView: 3,
					},
					1024: {
						slidesPerView: 4,
					},
					1280: {
						slidesPerView: columns,
					}
				}
			});

	   }

		/* Products carousel
		----*/

			function makeProductCarousel(products,sidebar){

				if (typeof products != 'undefined' && products != null) {

					var ID = uniqueID();

					$(products)
					.addClass('swiper-wrapper')
					.addClass('enova-carousel');

					$(products).find('.product').addClass('swiper-slide');
					$(products).wrap('<div class="swiper swiper-'+ID+'"></div>');

					$(products).parent().wrap('<div class="swiper-container"></div>');
					$(products).parents('.swiper-container').attr('data-arrows-pos',"top-right");

					$('<div id="prev-'+ID+'" class="swiper-button swiper-button-prev"></div><div id="next-'+ID+'" class="swiper-button swiper-button-next"></div>').insertAfter($(products).parent());

					var items     = sidebar ? 5 : 6,
						items1024 = sidebar ? 3.4 : 4.4;

					if ($(products).parent().hasClass('cross-sells')) {items1024 = items = 5;}

					var swiper = new Swiper('.swiper-'+ID, {
						direction:'horizontal',
						loop: false,
						spaceBetween: 16,
						slidesPerView: items,
						grabCursor: true,
						autoHeight: true,
						navigation: {
						    nextEl: '#'+$(products).parents('.swiper-container').find('.swiper-button-next').attr('id'),
						    prevEl: '#'+$(products).parents('.swiper-container').find('.swiper-button-prev').attr('id'),
						},
						breakpoints: {
							200: {
								slidesPerView: 2.2,
								spaceBetween: 8,
							},
							375: {
								slidesPerView: 2.4,
								spaceBetween: 8,
							},
							425: {
								slidesPerView: 2.4,
								spaceBetween: 8,
							},
							540: {
								slidesPerView: 1.8,
								spaceBetween: 8,
							},
							768: {
								slidesPerView: 3.4,
								spaceBetween: 16,
							},
							1024: {
								slidesPerView: items1024,
							},
							1280: {
								slidesPerView: items,
							}
						}
					});

				}
			}

			var sidebar = $('.post-layout-single.sidebar-active').length ? true : false;

			var targets = [
				'.related > .loop-products',
				'.up-sells > .loop-products',
				'.cross-sells > .loop-products',
				'.history-products > .loop-products',
			];

			for (var i = 0; i < targets.length; i++) {
				makeProductCarousel(document.querySelector(targets[i]),sidebar);
			}

		/* Posts carousel
		----*/

			if ($('#related-posts').length) {

				var reltatedPosts = $('#related-posts').addClass('enova-carousel'),
					items     	  = reltatedPosts.parents('.swiper-container').data('columns'),
					items1024 	  = reltatedPosts.parents('.swiper-container').data('tab-land-columns'),
					items768 	  = 2;

					if($('#related-posts .post').length > 2){
						items1024 += 0.4;
						items768  += 0.4;
					}

				$('#related-posts .post').addClass('swiper-slide');

				var swiper = new Swiper('#'+reltatedPosts.parent().attr('id'), {
					direction:'horizontal',
					loop: false,
					spaceBetween: 24,
					slidesPerView: items,
					grabCursor: true,
					autoHeight: true,
					navigation: {
					    nextEl: '#'+reltatedPosts.parents('.swiper-container').find('.swiper-button-next').attr('id'),
					    prevEl: '#'+reltatedPosts.parents('.swiper-container').find('.swiper-button-prev').attr('id'),
					},
					breakpoints: {
						200: {
							slidesPerView: 1.6,
							spaceBetween: 8,
						},
						375: {
							slidesPerView: 1.8,
							spaceBetween: 8,
						},
						425: {
							slidesPerView: 1.6,
							spaceBetween: 8,
						},
						540: {
							slidesPerView: items768,
							spaceBetween: 8,
						},
						768: {
							slidesPerView: items768,
						},
						1024: {
							slidesPerView: items1024,
						},
						1280: {
							slidesPerView: items,
						}
					}
				});

			}

	})(jQuery);

/* Header
----*/

	/* Submenu
	----*/

		(function($){

			"use strict";

			function submenuPosition(){

				$('.et-desktop .header-menu > .menu-item').each(function(){

					var $this = $(this);

					if ($this.children('.sub-menu:not(.megamenu)').length) {

						if( $this.offset().left + $this.width() + $this.children('.sub-menu').width() > $(window).innerWidth()){
							$this.addClass('submenu-left');
						} else {
							$this.removeClass('submenu-left');
						}

					}

				});

			}

			var currentUrl = window.location.href;

			$('.nav-menu').each(function(){

				$(this).children().each(function(){

					var menuItem = $(this);

					if (
						menuItem.children('a[href="'+currentUrl+'"]').length || 
						menuItem.children('ul').children('li').children('a[href="'+currentUrl+'"]').length ||
						(($('body.category').length || $('body.tag').length || $('body.single-post').length) && menuItem.children('a[href="'+$('body').data('blog-url')+'"]').length) ||
						(($('body.woocommerce').length || $('body.woocommerce-page').length) && menuItem.children('a[href="'+$('body').data('shop-url')+'"]').length)
						) {
						menuItem.addClass('active').siblings().removeClass('active');
					}

				});

			});

			submenuPosition();
			$(window).resize(submenuPosition);

			$('.nav-menu:not(".megamenu-demo")').each(function(){

				var $this  		= $(this),
					menuEffect  = (!$this.parent().hasClass('menu-hover-none') && !$this.parent().hasClass('menu-hover-underline-default')) ? true : false;

				if ($this.parents('.header').length) {

					if (window.location.href.indexOf("data_blog") > -1) {
						$this.children('li.blog').addClass("active").siblings().removeClass("active");
					} else if (window.location.href.indexOf("data_shop") > -1) {
						$this.children('li.shop').addClass("active").siblings().removeClass("active");
					} else if ($('body').hasClass('single-header') || !$this.children('li.active').length) {
						$this.children('li').first().addClass('active');
					}
				}

				$this.children('.depth-0').hover(
					function(){
						var li = $(this);
						setTimeout(function(){li.addClass('hover');},200);
					},
					function(){
						$(this).removeClass('hover');
					}
				);

				if (menuEffect) {

					var active          	= '',
						activeOffset        = 0,
						currentMenuItem     = $this.children('li.active').eq(0);

					if (typeof(currentMenuItem) == "undefined" || !currentMenuItem.length) {
						// Add active to first item
                        $this.children('li').first().addClass('active');
					}

					currentMenuItem = $this.children('li.active').eq(0);
					currentMenuItem.siblings().removeClass('active');

					if (currentMenuItem.length) {
						active       = currentMenuItem;
						activeOffset = active.children('a').find('.effect').offset().left;

						if (isRTL) {
							activeOffset += active.children('a').find('.effect').width();
						}

						if (active.length) {
							active = active.children('a').find('.effect');
						} else {
							active = $this.children('li:first-child').children('a').find('.effect')
						}

						$(window).resize(function(){
							activeOffset = $this.children('li.active').children('a').find('.effect').offset().left;
							if (isRTL) {
								activeOffset += $this.children('li.active').children('a').find('.effect').width();
							}
						});

					}

					$.each($this.children('.depth-0'),function(){

						var li 		= $(this),
							effect  = li.children('a').find('.effect'),
							effectX = Math.round(effect.offset().left - activeOffset),
							effectW = Math.round(effect.outerWidth());

						if (isRTL) {
							effectX += effect.width();
						}

						li.on('mouseover touchstart',function(){

							gsap.to(active,1, {
								x:effectX,
								width:effectW,
								ease:"elastic.out(1, 1.15)"
							});

							li.addClass('in').siblings().removeClass('in');

							if (li.hasClass('active')) {
								li.removeClass('using');
							} else {
								li.parent().children('li.active').addClass('using');
							}

						});

					});


					$this.on('mouseleave',function(){

						var width = ($this.parent().hasClass('menu-hover-overline') || $this.parent().hasClass('menu-hover-underline')) ? Math.round($this.find('li.active .mi-link .txt').outerWidth()) : Math.round($this.find('li.active .mi-link').outerWidth()),
							x     = ($this.parent().hasClass('menu-hover-overline') || $this.parent().hasClass('menu-hover-underline')) ? Math.round($this.find('li.active .mi-link .txt').offset().left - activeOffset) : Math.round($this.find('li.active .mi-link').offset().left - activeOffset);

						if (isRTL) {
							x += width;
						}

						gsap.to(active,1, {
							x:x,
							width:width,
							ease:"elastic.out(1, 1.15)"
						});

						$this.find('.in').removeClass('in');
						$this.find('.using').removeClass('using');
					});


				}

			});


		})(jQuery);

	/* Sticky
	----*/

		(function($){

			"use strict";

			var didScroll = false;

			function stickyHeader(header,changeHeaderOn) {

		    	if( !didScroll ) {
	                didScroll = true;
	                scrollPage(header,changeHeaderOn);
	            }

		        window.addEventListener( 'scroll', function( event ) {
		            if( !didScroll ) {
		                didScroll = true;
		                scrollPage(header,changeHeaderOn);
		            }
		        }, false );

		    }

		    function scrollPage(header,changeHeaderOn) {
		        var sy = (window.pageYOffset || document.documentElement.scrollTop);

	    		if ( changeHeaderOn > 0 && sy >= changeHeaderOn ) {
	        		header.addClass('active');
	        	} else {
	        		header.removeClass('active');
	        	}

		        didScroll = false;
		    }

			$( '.header.sticky-true' ).each(function(){
				var $this 		   = $(this);
		        var changeHeaderOn = $this.outerHeight();
			    stickyHeader($this,changeHeaderOn);
			    $('<div class="header-placeholder" style="height:'+$this.outerHeight()+'px;"></div>').insertAfter($this);

			});

		})(jQuery);

	/* Toggles
	----*/

		/* Header search
		----*/

			(function($){
	
				"use strict";

				$('.header-search').each(function(){

					var $this  = $(this),
						toggle = $this.find('.search-toggle'),
						close  = $this.find('.close-toggle'),
						box    = $this.find('.search-box'),
						start  = $this.find('.start'),
						end    = $this.find('.end'),
						icon   = $this.find('.search-icon'),
						input  = $this.find('input[type="text"]'),
						isOpen = false;

					var tl = new gsap.timeline({paused: true});

					tl.to(box,0, {
					  visibility:'visible', immediateRender:false
					},'+=0.2');

					tl.to(start,1.2, {
					  morphSVG:{shape:end, shapeIndex:8},
					  ease:"elastic.out(1, 0.75)"
					});

					tl.from(icon,1.2, {
					  x:'12px',
					  ease:"elastic.out(1, 0.75)"
					},'-=1.2');

					tl.add("open");

					tl.to(start,0.6, {
					  morphSVG:{shape:start},
					  ease:"elastic.out(1, 1.75)"
					},'+=0.2');

					tl.to(box,0.1, {
					  opacity:0,
					  ease:"sine.in"
				  	},'-=0.45');

					tl.to(box,0, {
					  visibility:'hidden', immediateRender:false
					});

					tl.add("close");

					tl.to(start,0.1, {
					  morphSVG:{shape:start}, immediateRender:false
					});

					tl.to(box,0.1, {
					  opacity:0, immediateRender:false
					});

					tl.to(box,0, {
					  visibility:'hidden', immediateRender:false
					});

					tl.add("hide");

					toggle.on('click',function(e){

						box.removeClass('hide');

						toggle.addClass('active');

						input.val('');

						if (isOpen==false) {

							tl.progress(0);
							tl.tweenTo("open");

							setTimeout(function(){
								input.focus();
							},700);

							isOpen=true;

						}

					});

					close.on('click',function(e){

						toggle.removeClass('active');

						if (close.hasClass('hide')) {

							box.addClass('hide');

							e.preventDefault();
							input.val('');

							tl.seek("close");
							tl.play();

							close.removeClass('hide');

							isOpen=false;

						} else {

							if (!input.val()) {
								tl.tweenTo("close");
								isOpen=false;
							}
						}

					});

					$this.find('#searchsubmit').on('click',function(e){
						if (!input.val()) {
							e.preventDefault();
							input.val('');
							tl.tweenTo("close");
						}
					});

				});

			})(jQuery);

		/* Shopping cart
		----*/

			(function($){
	
				"use strict";

				$('.mini-cart').each(function(){
					var element      = this,
						$this   	 = $(element),
						toggle  	 = $this.find('.cart-toggle');

					toggleBack(element,toggle);
				});

			})(jQuery);

		/* Language switcher
		----*/

			(function($){
	
				"use strict";

				$('.wpml-ls-legacy-dropdown-click').each(function(){
					var $this = $(this);

					$this.find('.js-wpml-ls-item-toggle').on('click',function(){
						$this.find('.js-wpml-ls-sub-menu').toggleClass('active');
					});

				});

			})(jQuery);

		/* Login toggle
		----*/

			(function($){
		
				"use strict";

				$('.et-login').each(function(){

		            var element = this,
		                toggle  = $(element).find('.login-toggle');

		            toggleBack(element,toggle);
		            
		        });

		    })(jQuery);

		/* Widget navigation
		----*/

			(function($){
	
				"use strict";

				// Animate sidebar
				var sidebarArea    = $('.layout-sidebar'),
					sidebarOverlay = $('<div class="sidebar-layout-overlay"></div>').insertAfter(sidebarArea);

				$('.content-sidebar-toggle').on('click',function(e){

					e.preventDefault();

					sidebarArea.toggleClass('active');
					sidebarOverlay.toggleClass('active');

					if ($(this).hasClass('active')) {
						setTimeout(function(){$('#et-content').removeAttr('style');},200);
						$('.sticky-dashboard').addClass('active');
					} else {
						$('#et-content').css('z-index',99);
						$('.sticky-dashboard').removeClass('active');

					}

				});

				$('.sidebar-layout-overlay').on('click',function(e){
					if(e.target !== e.currentTarget) return;
					sidebarArea.toggleClass('active');
					sidebarOverlay.toggleClass('active');
					setTimeout(function(){$('#et-content').removeAttr('style');},200);
					$('.sticky-dashboard').toggleClass('active');
				});
				
				new XTouchSwipe(document.body);
				document.body.addEventListener('x-swipe', event => {
					const direction = event.detail;
					if(((isRTL == false && direction === 'left') || (isRTL && direction === 'right')) && sidebarArea.hasClass('active')) {
						sidebarArea.removeClass('active');
						sidebarOverlay.removeClass('active');
						setTimeout(function(){$('#et-content').removeAttr('style');},200);
						$('.sticky-dashboard').toggleClass('active');
					}
				});

			})(jQuery);

		/* Product search toggle
		----*/

			(function($){
		
				"use strict";

				$('.et-product-search-toggle').each(function(){

		            var element      = this,
		                toggle  	 = $(element).find('.search-toggle'),
		                toggleFilter = $(element).find('.filter-toggle'),
		                box     	 = $(element).find('.search-box'),
		                boxFilter    = $(element).find('.filter-box'),
		                off     	 = $(element).find('.search-toggle-off'),
		                placeholder  = $(element).find('.toggle-placeholder'),
		                offFilter    = $(element).find('.filter-toggle-off');

		            var	addToCart = $('.single_variation_wrap').length ? $('.single_variation_wrap') : $('form.cart:not(.variations_form)');

		            toggle.on('click',function(){
		            	box.toggleClass('active');
		            	box.find('input[type="search"]').focus();
		            	$('.sticky-dashboard').removeClass('active');

				    	if (addToCart.length) {
							addToCart.addClass('transform');
						}

		            });

		            off.on('click',function(){
		            	box.toggleClass('active');
		            	$('.sticky-dashboard').addClass('active');
		            	if (addToCart.length) {
							addToCart.removeClass('transform');
						}
		            	$(element).find('input[type="search"]').val('');
		            	$(element).find('.search-results').removeClass('active').html('');
		            });

		            toggleFilter.on('click',function(){
		            	boxFilter.toggleClass('active');
		            	$('.sticky-dashboard').removeClass('active');
		            	if (addToCart.length) {
							addToCart.addClass('transform');
						}
		            });

		            offFilter.on('click',function(){
		            	boxFilter.toggleClass('active');
		            	$('.sticky-dashboard').addClass('active');
		            	if (addToCart.length) {
							addToCart.removeClass('transform');
						}
		            });

		            placeholder.on('click',function(){
		            	toggle.trigger('click');
		            });
		            
		        });

		    })(jQuery);

		/* Product search focus
		----*/

			(function($){
		
				"use strict";

				$('.product-search input.search').focusin(function(){
		            $(this).parents('div.product-search').addClass('focus');
		        });

		        $('.product-search input.search').focusout(function(){
		            $(this).parents('div.product-search').removeClass('focus');
		        });

		    })(jQuery);

	/* Sticky dashboard
	----*/
		
		(function($){

			"use strict";

			if ($('.sticky-dashboard').length) {

				var	addToCart = $('.single_variation_wrap').length ? $('.single_variation_wrap') : $('form.cart:not(.variations_form)');

				if($('.et-product-search-toggle').length){

					$('.sticky-dashboard .product-search-toggle').on('click',function(e){
						e.preventDefault();
						$('.et-product-search-toggle .search-toggle').trigger('click');
					});

					if ($('.et-product-search-toggle .filter-toggle').length) {

						$('.sticky-dashboard .vehicle-filter-toggle').on('click',function(e){
							e.preventDefault();
							if (addToCart.length) {
								addToCart.addClass('transform');
							}
							$('.et-product-search-toggle .filter-toggle').trigger('click');
						});

					} else {
						$('.sticky-dashboard .vfilter-toggle').addClass('hidden');
					}

				} else {
					$('.sticky-dashboard .product-search').addClass('hidden');
					$('.sticky-dashboard .vfilter-toggle').addClass('hidden');
				}

				$('.sticky-dashboard').addClass('active');

				$('.sticky-dashboard .account a[href="#"]').on('click',function(e){
					e.preventDefault();

					var placeholder = '<ul class="woocommerce-MyAccount-navigation">';

					for (var i = 1; i < 5; i++) {
						placeholder += '<li class="woocommerce-MyAccount-navigation-link placeholder"><svg viewBox="0 0 343 49"><path d="M0,0H349V49H0V0Z" /></svg></li>';
					}

					placeholder += '</ul>';

					$('.sticky-dashboard').removeClass('active');

					if (addToCart.length) {
						addToCart.addClass('transform');
					}

					$('body').append('<div class="ajax my-account-nav-wrapper active"><span class="dashboard-mobile-toggle-off"></span><div class="inner">'+placeholder+'</div></div>');

					$.ajax({
		                url:controller_opt.ajaxUrl,
		                type: 'post',
		                data: {'action':'fetch_dashboard_myaccount'},
		                success: function(data) {
		                    try {
		                        if(data){
		                           $('.ajax.my-account-nav-wrapper > .inner').html(data);
		                        }
		                    } catch(e) {
		                        console.log(e);
		                    }
		                },
		                error:function () {
		                    console.log(controller_opt.error);
		                }
		            });				
				});

				$('body').on('click','.ajax.my-account-nav-wrapper .dashboard-mobile-toggle-off',function(){
					$('.ajax.my-account-nav-wrapper').remove();
					$('.sticky-dashboard').addClass('active');
					if (addToCart.length) {
						addToCart.removeClass('transform');
					}
				});

				if(typeof($.cookie('vehicle')) != 'undefined'){
					$('.sticky-dashboard .vehicle-filter-toggle').addClass('has-vehicle');
				}

				function fetchDashboardCategories(id = false){

					var data = {'action':'fetch_dashboard_categories'};

					if (id) {
						data['term_id'] = id;
					}

					$.ajax({
		                url:controller_opt.ajaxUrl,
		                type: 'post',
		                data: data,
		                success: function(data) {
		                    try {
		                        if(data){
		                           $('.modal-categories-wrapper > .inner').html(data);
		                           lazyLoad(document.getElementById('modal-categories-wrapper'));
		                        }
		                    } catch(e) {
		                        console.log(e);
		                    }
		                },
		                error:function () {
		                    console.log(controller_opt.error);
		                }
		            });	
				}

				var placeholder = '<ul class="loop-categories">';

					for (var i = 1; i < 7; i++) {
						placeholder += '<li class="category-item placeholder"><svg viewBox="0 0 200 140"><path d="M0,0H200V140H0V0Z" /></svg></li>';
					}

					placeholder += '</ul>';



				$('.sticky-dashboard .categories a').on('click',function(e){
					e.preventDefault();
					$('.sticky-dashboard').removeClass('active');

					if (addToCart.length) {
						addToCart.addClass('transform');
					}

					$('body').append('<div id="modal-categories-wrapper" class="ajax modal-categories-wrapper active"><span class="categories-mobile-toggle-off"></span><div class="inner">'+placeholder+'</div></div>');

					fetchDashboardCategories();			
				});

				$('body').on('click','.ajax.modal-categories-wrapper a',function(e){
					var id = $(this).attr('data-id');
					if (typeof(id) != 'undefined') {
						e.preventDefault();
						$('.modal-categories-wrapper > .inner').html(placeholder);
						fetchDashboardCategories(id);
					} else if($(this).hasClass('back')) {
						e.preventDefault();
						$('.modal-categories-wrapper > .inner').html(placeholder);
						fetchDashboardCategories();
					} else {

						var activeParams = getParams();

						if (activeParams) {
							e.preventDefault();

							createURL($(this).attr('href'),activeParams);
						}
					}
				});

				$('body').on('click','.ajax.modal-categories-wrapper .categories-mobile-toggle-off',function(){
					$('.ajax.modal-categories-wrapper').remove();
					$('.sticky-dashboard').addClass('active');

					if (addToCart.length) {
						addToCart.removeClass('transform');
					}
				});

			}
			

		})(jQuery);


		(function($){

			"use strict";

			if ($('body').hasClass('logged-in') && ($('.login-box').length || $('.logged-in.info-wrap').length)) {


				$.ajax({
	                url:controller_opt.ajaxUrl,
	                type: 'post',
	                data: {'action':'fetch_user_info'},
	                success: function(data) {
	                    try {
	                        if(data){

	                            data = JSON.parse(data);

	                            if (data['user']) {

	                            	if ($('.et-login .info span:first-child').length) {
	                            		$('.et-login .info span:first-child').text(data['user']);
	                            	} else {
	                            		$('.et-login .info').append('<span>'+data['user']+'</span>');
	                            	}

	                            	if ($('.logged-in.info-wrap .info span:first-child').length) {
	                            		$('.logged-in.info-wrap .info span:first-child').text(data['user']);
	                            	} else {
	                            		$('.logged-in.info-wrap .info').append('<span>'+data['user']+'</span>');
	                            	}

	                            }

	                            if (data['email']) {


	                            	if ($('.et-login .info span:nth-child(2)').length) {
	                            		$('.et-login .info span:nth-child(2)').text(data['email']);
	                            	} else {
	                            		$('.et-login .info').append('<span>'+data['email']+'</span>');
	                            	}

	                            	if ($('.logged-in.info-wrap .info span:last-child').length) {
	                            		$('.logged-in.info-wrap .info span:last-child').text(data['email']);
	                            	} else {
	                            		$('.logged-in.info-wrap .info').append('<span>'+data['email']+'</span>');
	                            	}

	                            }

	                        }
	                    } catch(e) {
	                        console.log(e);
	                    }
	                },
	                error:function () {
	                    console.log(controller_opt.error);
	                }
	            });
			}

		})(jQuery);

/* Main
----*/

	(function($){

		"use strict";

		$.fn.footerReveal=function(o){var t=$(this),e=t.prev(),i=$(window),s=$.extend({shadow:!0,shadowOpacity:.8,zIndex:-100},o);$.extend(!0,{},s,o);return t.outerHeight()<=i.outerHeight()&&t.offset().top>=i.outerHeight()&&(t.css({"z-index":s.zIndex,position:"fixed",bottom:0}),s.shadow&&e.css({"-moz-box-shadow":"0 20px 30px -20px rgba(0,0,0,"+s.shadowOpacity+")","-webkit-box-shadow":"0 20px 30px -20px rgba(0,0,0,"+s.shadowOpacity+")","box-shadow":"0 20px 30px -20px rgba(0,0,0,"+s.shadowOpacity+")"}),i.on("load resize footerRevealResize",function(){t.css({width:e.outerWidth()}),e.css({"margin-bottom":t.outerHeight()})})),this};
		
		function stickyFooter(){
			var footer = $('.footer.sticky-true');
			if (typeof(footer) != 'undefined' && footer.length) {
				$('.page-content-wrap').addClass('disable');
				footer.footerReveal({ shadow: false, zIndex: -101 });
				footer.addClass('active');
			}
		}

		function mobileNavigation(){

			// Animate mobile
			var mobileContainer = $('.mobile-container');
			var	addToCart       = $('.single_variation_wrap').length ? $('.single_variation_wrap') : $('form.cart:not(.variations_form)');

			$('<div class="mobile-container-overlay"></div>').insertAfter(mobileContainer);

			$('body').on('click','.mobile-toggle',function(){
				mobileContainer.toggleClass('active');
				$('.sticky-dashboard').toggleClass('active');
				if (addToCart.length) {
					addToCart.toggleClass('transform');
				}
			});

			$('body').on('click','.mobile-container-overlay',function(){
				mobileContainer.removeClass('active');
			});
			
			new XTouchSwipe(document.body);
			document.body.addEventListener('x-swipe', event => {
				const direction = event.detail;
				if(direction === 'left' && mobileContainer.hasClass('active')) {
					mobileContainer.removeClass('active');
					$('.sticky-dashboard').addClass('active');
					if (addToCart.length) {
						addToCart.removeClass('transform');
					}
				}
			});

			$('.mobile-menu .menu-item-has-children > a').each(function(){
				var $link = $(this);
				if ($link.attr( "href" ) == "#") {
					$link.on('click',function(e){
						e.preventDefault();
						$link.parent().toggleClass('active');
						isolate($link);
					});
				} else {
					$link.find('.arrow').on("click", function(e){
						e.preventDefault();
						var $this = $(this);
						// $link.parent().toggleClass('active');
						isolate($link);
					});
				}
			});

			if (window.matchMedia('(max-width: 767px)')) {
				$('.et-menu .menu-item-has-children > a').each(function(){
					var $link = $(this);
					if ($link.attr( "href" ) == "#") {
						$link.on('click',function(e){
							e.preventDefault();
							$link.find('.arrow').toggleClass('active');
							$link.next('ul').stop().slideToggle(200);
						});
					} else {
						$link.find('.arrow').on("click", function(e){
							e.preventDefault();
							var $this = $(this);
							$this.toggleClass('active');
							$link.next('ul').stop().slideToggle(200);
						});
					}
				});
			}

		}

		function removeVariablesExceptCurrency(url) {
		    // Parse the URL
		    let urlParts = url.split('?');
		    if (urlParts.length < 2) {
		        // No query parameters
		        return url;
		    }

		    let baseUrl = urlParts[0];
		    let queryString = urlParts[1];

		    // Parse the query string into key-value pairs
		    let queryParams = {};
		    queryString.split('&').forEach(function(param) {
		        let keyValue = param.split('=');
		        let key = keyValue[0];
		        let value = keyValue[1];
		        queryParams[key] = value;
		    });

		    // Remove all variables except 'alg_currency'
		    let filteredParams = {};
		    if ('alg_currency' in queryParams) {
		        filteredParams['alg_currency'] = queryParams['alg_currency'];
		    }

		    // Reconstruct the URL
		    let newQueryString = Object.keys(filteredParams).map(function(key) {
		        return key + '=' + filteredParams[key];
		    }).join('&');

		    let newUrl = $('body').attr('data-url');
		    if (newQueryString !== '') {
		        newUrl += '?' + newQueryString;
		    }

		    return newUrl;
		}

		function lang_curr_Toggles(){

			var curLang = '';
			var img     = $('.language-switcher .current-lang img');
			var dataObj = getParams();
			var dataArr = (decodeURIComponent(window.location.href)).split('/');

			if (dataObj && dataObj['lang']) {curLang = dataObj['lang']}

			$('.language-switcher').each(function(index){

				var element      = this,
					$this   	 = $(element),
					toggle  	 = $this.find('.language-toggle');

				if (index == 0 && curLang == '') {

					$this.find('a').each(function(){
						var lang = $(this).attr('lang').split('-').shift();

						if (dataArr.includes(lang)) {
							curLang = lang;
							img = $(this).find('img');
						}

					});

				}

				if (img != '' && typeof(img) != 'undefined' && img.length) {
					var html = $this.find('.language-toggle .current-lang').text();
					if (!$this.find('.language-toggle .current-lang img').length) {
						$this.find('.language-toggle .current-lang').html('<img src="'+img.attr('src')+'" width="16" height="16">'+html);
					}
				}

				if (curLang != '') {
					$this.find('a[lang*="'+curLang+'"]').parent().addClass('current-lang').siblings().removeClass('current-lang');
					$this.find('.language-toggle .current-lang').html('<img src="'+img.attr('src')+'" width="16" height="16">'+curLang);
				}

				toggleBack(element,toggle);

			});

			$('.currency-switcher').each(function(){


		    	var element = this,
	                toggle  = $(element).find('.currency-toggle');

	            $(element).find('a').each(function(){
	            	$(this).attr('href',removeVariablesExceptCurrency($(this).attr('href')));
	            });

	            if (dataObj && Object.keys(dataObj).length != 0 && dataObj['alg_currency']) {
	            	if (!toggle.find('.highlighted-currency').length) {
		            	$('<span class="highlighted-currency">'+$(element).find('.currency-list a[id*="'+dataObj['alg_currency']+'"]').text()+'</span>').insertBefore(toggle.not('.close-toggle').find('.arrow'));
		            }
		            toggle.on('click',function(){
		            	toggle.find('.highlighted-currency').remove();
		            	$('<span class="highlighted-currency">'+$(element).find('.currency-list a[id*="'+dataObj['alg_currency']+'"]').text()+'</span>').insertBefore(toggle.not('.close-toggle').find('.arrow'));
		            });
	            } else {
	            	if (!toggle.find('.highlighted-currency').length) {
            			if (localStorage.getItem("currency")) {
		            		$('<span class="highlighted-currency">'+localStorage.getItem("currency")+'</span>').insertBefore(toggle.not('.close-toggle').find('.arrow'));
						} else {
		            		$('<span class="highlighted-currency">'+$(element).find('.currency-list a:first-child').text()+'</span>').insertBefore(toggle.not('.close-toggle').find('.arrow'));
						}
		            }
		            toggle.on('click',function(){
		            	toggle.find('.highlighted-currency').remove();
		            	$('<span class="highlighted-currency">'+$(element).find('.currency-list a:first-child').text()+'</span>').insertBefore(toggle.not('.close-toggle').find('.arrow'));
		            });
	            }

	            if (curLang != '') {

	            	$(element).find('a').each(function(){
	            		var href = $(this).attr('href');
	            		var href = href.split('?');
	            		var href  = href[0]+curLang+'/'+'?'+href[1];
	            		$(this).attr('href',href);

	            	});

				}

	            toggleBack(element,toggle);
	            

			});
		}

		function megamenuTab(){

			$('.megamenu[data-tabbed="true"]').each(function(){
				var megamenu = $(this);

				if(!megamenu.find('.tabset').length){

					var tabset = '<div class="tabset megamenu-tabset">';

					megamenu.find('.megamenu-tab-item').wrapAll('<div class="megamenu-tabs-container tabs-container" />');

					megamenu.find('.megamenu-tab-item').each(function(){
						var $this = $(this),
							title = $this.attr('data-tab-title'),
							icon  = $this.attr('data-tab-icon');

						tabset += '<div class="tab-item megamenu-tab-item">';
							if (typeof(icon) != "undefined" && icon.length) {
								tabset += '<span class="icon megamenu-icon" style="-webkit-mask: url('+icon+');mask: url('+icon+');"></span>';
							}
							if (typeof(title) != "undefined" && title.length) {
								tabset += '<span class="txt">'+title+'</span><span class="arrow"></span>';
							}
						tabset += '</div>';
					});

					tabset += '</div>';

					$(tabset).insertBefore(megamenu.find('.megamenu-tabs-container'));

					var tabSet            = megamenu.find('.tabset'),
						tabs     		  = tabSet.find('.tab-item'),
						tabsQ    		  = tabs.length,
						tabsDefaultWidth  = 0,
						tabsDefaultHeight = 0,
						tabsContent 	  = megamenu.find('.megamenu-tabs-container .tab-content'),
						action      	  = 'click';

					if(!tabs.hasClass('active')){
						tabs.first().addClass('active');
					}

					tabs.each(function(){

						var $thiz = $(this);

						if ($thiz.hasClass('active')) {
							$thiz.siblings().removeClass("active");
							tabsContent.eq($thiz.index()).addClass('active').siblings().removeClass('active');
						}

					});


					if(tabsQ >= 2){

						if (action == 'click') {
							tabs.on('click', function(event){
								event.stopImmediatePropagation();

								var $self = $(this);

								if(!$self.hasClass("active")){

									$self.addClass("active");

									$self.siblings()
									.removeClass("active");

									tabsContent.removeClass('active');
									tabsContent.eq($self.index()).addClass('active');
									
								}
							});
						} else {
							tabs.on('mouseover', function(event){

								event.stopImmediatePropagation();

								var $self = $(this);

								if(!$self.hasClass("active")){

									$self.addClass("active");

									$self.siblings()
									.removeClass("active");

									tabsContent.removeClass('active');
									tabsContent.eq($self.index()).addClass('active');

								}
								
							});
						}
						
					}

				}

			});
		}

		function mobileContainerTabs(){


			if ($('.mobile-tab-item').length) {
				
				var tabset = '<div class="tabset mobile-tabset">';

				$('.et-mobile').find('.mobile-tab-item').wrapAll('<div class="mobile-tabs-container tabs-container" />');

				$('.et-mobile').find('.mobile-tab-item').each(function(){
					var $this = $(this),
						title = $this.attr('data-mob-tab-title'),
						icon  = $this.attr('data-mob-tab-icon');

					tabset += '<div class="tab-item mobile-tab-item">';
						if (typeof(icon) != "undefined" && icon.length) {
							tabset += '<span class="icon mobile-icon" style="-webkit-mask: url('+icon+') no-repeat 50% 50%;mask: url('+icon+') no-repeat 50% 50%;"></span>';
						}
						if (typeof(title) != "undefined" && title.length) {
							tabset += '<span class="txt">'+title+'</span>';
						}
					tabset += '</div>';
				});

				tabset += '</div>';

				$(tabset).insertBefore($('.et-mobile').find('.mobile-tabs-container'));

				var tabs     		  = $('.et-mobile').find('.tab-item'),
					tabsQ    		  = tabs.length,
					tabsDefaultWidth  = 0,
					tabsDefaultHeight = 0,
					tabsContent 	  = $('.et-mobile').find('.tab-content'),
					action      	  = 'click';

				var tabSet = $('.et-mobile').find('.tabset');

				if(!tabs.hasClass('active')){
					tabs.first().addClass('active');
				}

				tabs.each(function(){

					var $thiz = $(this);

					if ($thiz.hasClass('active')) {
						$thiz.siblings().removeClass("active");
						tabsContent.eq($thiz.index()).addClass('active').siblings().removeClass('active');
					}

				});

				if(tabsQ >= 2){

					tabs.on('click', function(event){
						event.stopImmediatePropagation();

						var $self = $(this);

						if(!$self.hasClass("active")){

							$self.addClass("active");

							$self.siblings()
							.removeClass("active");

							tabsContent.removeClass('active');
							tabsContent.eq($self.index()).addClass('active');
							
						}
					});
					
				}

			}


		}

		function megamenuPos(){

			$('.megamenu[data-width="grid"]:not(.megamenu-sidebar)').each(function(){

			    var $this = $(this),
		    		leftValue = $this.parents('.e-con-inner').length ? $this.parents('.e-con-inner').offset().left : $this.parents('.e-con').children().eq(0).offset().left,
		    		parentOffset = $this.parent().offset().left;
			    	leftValue = Math.abs(parentOffset - leftValue);

					$this.attr('style', 'left: -' + Math.abs(leftValue) + 'px !important');


			});

			$('.megamenu[data-width="100"]:not(.megamenu-sidebar)').each(function(){

			    var $this     = $(this),
		    		leftValue = $this.parent().offset().left;
					$this.attr('style', 'left: -' + leftValue + 'px !important;width: ' + $(window).width() + 'px; min-width: ' + $(window).width() + 'px;');

			});

			if(!$('body').hasClass('single-megamenu')){

				$('.megamenu:not([data-width="100"]):not([data-width="grid"]):not(.megamenu-sidebar)').each(function(){

				    var $this = $(this),
			    		offset = $this.data('offset'),
			    		position = $this.data('position'),
			    		width = $this.data('width');

			    		$this.attr('style', 'width:' + Math.round((width/100)*1320) + 'px !important;min-width:' + Math.round((width/100)*1320) + 'px !important');

			    		if(typeof(offset) != "undefined"){

				    		if (position == "left" || position == "center") {

				    			if (isRTL) {
				    				$this.css('margin-right',offset+'px');
				    			} else {
				    				$this.css('margin-left',offset+'px');
				    			}

				    		} else {

				    			if (isRTL) {
				    				$this.css('margin-left',offset+'px');
				    			} else {
				    				$this.css('margin-right',offset+'px');
				    			}

				    		}

			    		} else if(position == "center"){

			    			if (isRTL) {
			    				$this.css('margin-right','-'+ Math.round((width/100)*1320)/2+'px');
			    			} else {
			    				$this.css('margin-left','-'+ Math.round((width/100)*1320)/2+'px');
			    			}

			    		}

				});

			}

			$('.megamenu.megamenu-sidebar').each(function(){

			    var $this  = $(this),
		    		cWidth = $this.parents('.e-con-inner').length ? $this.parents('.e-con-inner').width() : $this.closest('.e-con-inner').width(),
		    		parentWidth = $this.parents('.elementor-widget-container').width() - 8;
					$this.attr('style', 'width:' + (cWidth - parentWidth) + 'px !important');

			});


		}

		function megamenuHoverCheck(){
			$('.mm-ajax').each(function(){
				if ($(this).find('.sub-menu').length) {
					$(this).children('.mi-link').removeClass('loading-menu');
				}

				$(this).on('mouseenter',function(){
					if (!$(this).find('.sub-menu').length) {
						$(this).children('.mi-link').addClass('loading-menu');
					} else {
						$(this).children('.mi-link').removeClass('loading-menu');
					}
				});
			});
		}

		function animateBoxBack(box){

			var $this  = jQuery(box),
				width  = $this.width(),
				height = $this.height(),
				ratio  = Math.round(100*(height/width)),
				svg    = $this.find('.box-back'),
				path   = svg.find('path');

			// get svg viewBox
			var viewBox = box.querySelector('.box-back').getAttribute('viewBox');

			var viewBoxValues = viewBox.split(' ');

			viewBoxValues  = viewBoxValues.splice(2, 2);

			var replace = viewBoxValues[1];

			var start    = path.attr('d'),
				startC   = path.attr('data-dclone'),
				end      = path.attr('data-end'),
				original = path.attr('data-original');

			start  = start.replace(new RegExp((replace-10),"g"),(ratio-10));
			start  = start.replace(new RegExp(replace,"g"),ratio);
			startC = startC.replace(new RegExp((replace-10),"g"),(ratio-10));
			startC = startC.replace(new RegExp(replace,"g"),ratio);
			end    = end.replace(new RegExp(replace,"g"),ratio);

			if (typeof(original) != 'undefined') {
				original = original.replace(new RegExp(replace,"g"),ratio);
			}

			box.querySelector('.box-back').setAttribute('viewBox','0 0 100 '+ratio);

			path.attr('d',start);
			path.attr('data-end',end);
			path.attr('data-dclone',startC);

			if (typeof(original) != 'undefined') {
				path.attr('data-original',original);
			}

		}

		function buildAnimateBoxTimeline(tl,box,delay,animation,stagger,content){

			var path = box.find('.box-back path');

			tl.from(box,0.2, {
			  opacity:0,
			},delay);

			switch(animation){
				case 'top':

					tl.from(box,1.2, {
						y:-100,
						scaleY:0,
						rotationZ:8,
						force3D:true,
						transformOrigin:'right top',
						ease:"elastic.out(1, 0.5)"
					},'-=0.1');

				break;

				case 'bottom':

					tl.from(box,1.2, {
						y:100,
						scaleY:0,
						rotationZ:8,
						force3D:true,
						transformOrigin:'right bottom',
						ease:"elastic.out(1, 0.5)"
					},'-=0.1');
				
				break;

				case 'left':

					tl.from(box,1.2, {
						x:-100,
						scaleX:0,
						rotationZ:-8,
						force3D:true,
						transformOrigin:'left center',
						ease:"elastic.out(1, 0.5)"
					},'-=0.1');
				
				break;

				case 'right':

					tl.from(box,1.2, {
						x:100,
						scaleX:0,
						rotationZ:8,
						force3D:true,
						transformOrigin:'right center',
						ease:"elastic.out(1, 0.5)"
					},'-=0.1');
				
				break;
			}


			tl.to(path,1.2, {
			  morphSVG:{shape:path.attr('data-end'), shapeIndex:8},
			  ease:"elastic.out"
			},'-=1');

			switch(stagger){

				case "left":

					tl.from(content,{
					  	duration: 0.8,
						x:-50,
						stagger: 0.05,
						opacity:0,
						ease:"expo.out"
					},'-=1.1');

				break;

				case "right":

					tl.from(content,{
					  	duration: 0.8,
						x:50,
						stagger: 0.05,
						opacity:0,
						ease:"expo.out"
					},'-=1.1');

				break;

				case "top":

					tl.from(content,{
					  	duration: 0.8,
						y:-50,
						stagger: 0.05,
						opacity:0,
						ease:"expo.out"
					},'-=1.1');

				break;

				case "bottom":

					tl.from(content,{
					  	duration: 0.8,
						y:50,
						stagger: 0.05,
						opacity:0,
						ease:"expo.out"
					},'-=1.1');

				break;
			}

			tl.add('end');

		}

		function buildStaggerBoxTimeline(tl,delay,interval,stagger,content){

			switch(stagger){

				case "left":

					tl.from(content,{
					  	duration: 1.2,
						x:-100,
						stagger: interval,
						opacity:0,
						ease:"expo.out"
					},delay);

				break;

				case "right":

					tl.from(content,{
					  	duration: 1.2,
						x:100,
						stagger: interval,
						opacity:0,
						ease:"expo.out"
					},delay);

				break;

				case "top":

					tl.from(content,{
					  	duration: 1.2,
						y:-100,
						stagger: interval,
						opacity:0,
						ease:"expo.out"
					},delay);

				break;

				case "bottom":

					tl.from(content,{
					  	duration: 1.2,
						y:100,
						stagger: interval,
						opacity:0,
						ease:"expo.out"
					},delay);

				break;
			}

		}

		function disableParallax(){
			if ($(window).width() <= 1200) {
				$('.et-image.parallax').each(function(){
					$(this).addClass('parallax-off');
				});
			} else {
				$('.et-image.parallax').each(function(){
					$(this).removeClass('parallax-off');
				});
			}
		}

		function animateProductFlow(product){

			let CartLeft = 0,
				CartTop = 0;

			if ($('.et-desktop .cart-toggle').length) {
				CartLeft = $('.et-desktop .cart-toggle')[0].getBoundingClientRect().left + 30;
				CartTop = $('.et-desktop .cart-toggle')[0].getBoundingClientRect().top + 16;
			} else {
				CartLeft = $('.et-mobile .cart-toggle')[0].getBoundingClientRect().left + 25;
				CartTop = $('.et-mobile .cart-toggle')[0].getBoundingClientRect().top + 16;
			}

	        let clone   = product.find('img').clone().addClass('cart-product-animate'),
	            posL    = product.find('img')[0].getBoundingClientRect().left,
	            posT    = product.find('img')[0].getBoundingClientRect().top,
	            Iwidth  = product.find('img').width(),
	            Iheight = product.find('img').height();

	        $('body').append(clone);

	        $('.cart-product-animate').css({
	            'transform':'translate('+posL+'px,'+posT+'px)',
	            'width':Iwidth,
	            'height':Iheight
	        });

	        gsap.to('.cart-product-animate', {
	            x:CartLeft,
	            y:CartTop,
	            scale:0,
	        });


	        gsap.to('.cart-product-animate', {
	            opacity:0,
	            delay:0.1
	        });

	        setTimeout(function(){
	            $('.cart-product-animate').remove();
	        },700);
	    }

		function ajaxAddToCart(){
			$('.loop-products .product, ul.products .product').each(function(){

				var $this = $(this);
				var addToCard = $this.find('.ajax_add_to_cart');
				var productProgress = $this.find('.ajax-add-to-cart-loading');
				var addToCardEvent  = true;

				if (addToCard.hasClass('added')) {
					addToCardEvent  = false;
				}

				if (addToCard.attr('data-product_status') == 'outofstock') {
					addToCardEvent  = false;
				}

				if (addToCard.attr('data-product_type') == 'variable') {
					addToCardEvent  = false;
				}
				
				addToCard.on('click',function(){
					
					if (addToCardEvent == true) {
						var $self = $(this);
						
						productProgress.addClass('active');
						setTimeout(function(){
							animateProductFlow($this);
						},200);
						setTimeout(function(){
							productProgress.addClass('load-complete');
							gsap.to(productProgress.find('.tick'),0.2, {
							  opacity:1,
							});
							gsap.to(productProgress.find('.tick'),0.8, {
							  scale:1.15,
							  ease:"elastic.out"
							});
							productProgress.removeClass('active').removeClass('load-complete');
							addToCardEvent  = false;
						}, 1000);
					} else {
						alert(controller_opt.already);
					}
				});
			});
		}

		function listImages(){
			if ($(window).width() <= 720) {
				$('.list .loop-posts .post img').each(function(){

					var $this   			= $(this),
						dataRespSrc 	    = $this.attr('data-resp-src'),
						dataRespSrcOriginal = $this.attr('data-resp-src-original'),
						dataWidth           = $this.attr('data-width'),
						dataHeight          = $this.attr('data-height');
					
					if ($this.hasClass('lazy')) {
						$this.attr('src',dataRespSrc);
						$this.attr('data-src',dataRespSrcOriginal);	
					} else {
						$this.attr('src',dataRespSrcOriginal);
					}	
					$this.attr('width',dataWidth);
					$this.attr('height',dataHeight);

					$this.addClass('changed');

				});
			} else {
				$('.list .loop-posts .post img').each(function(){

					var $this = $(this);

					if ($this.hasClass('changed')) {

						var	dataRespSrc 	    = $this.attr('data-clone-resp-src'),
							dataRespSrcOriginal = $this.attr('data-clone-resp-src-original'),
							dataWidth           = $this.attr('data-clone-width'),
							dataHeight          = $this.attr('data-clone-height');
						
						if ($this.hasClass('lazy')) {
							$this.attr('src',dataRespSrc);
							$this.attr('data-src',dataRespSrcOriginal);	
						} else {
							$this.attr('src',dataRespSrcOriginal);
						}	
						$this.attr('width',dataWidth);
						$this.attr('height',dataHeight);

						$this.removeClass('changed');

					}

				});
			}
		}

		function toggle_hidden_variation_btn() {
			const resetVariationNodes = document.getElementsByClassName('reset_variations');

			if (resetVariationNodes.length) {

				Array.prototype.forEach.call(resetVariationNodes, function (resetVariationEle) {

					let observer = new MutationObserver(function () {

						if (resetVariationEle.style.visibility !== 'hidden') {

							resetVariationEle.style.display = 'block';

						} else {

							resetVariationEle.style.display = 'none';

						}

					});

					observer.observe(resetVariationEle, {attributes: true, childList: true});

				})

			}
		}

		function quickView(){

			$("body").on('click','.en-quick-view',function(e){

		    	$('.sticky-dashboard').removeClass('active');

		    	var	addToCart = $('.single_variation_wrap').length ? $('.single_variation_wrap') : $('form.cart:not(.variations_form)');

		    	if (typeof(addToCart) != "undefined" && addToCart.length) {
					addToCart.addClass('transform');
				}

				e.preventDefault();

				if (quickViewLoading) {return;}

				var quickView = $(this),
					product = quickView.attr('data-product');

				quickViewLoading = true;

				quickView.addClass('loading');

				$('body').append('<div class="qvw-loading"></div>');

				$.ajax({
	                url:controller_opt.ajaxUrl,
	                type: 'post',
	                data: {
	                	action:'quick_view',
	                	currency: controller_opt.currency,
	                	id:product,
	                },
	                success: function(data) {
	                	if (data.length) {

	                		$('.qvw-loading').remove();

							$('body').append(data);

							$('.quick-view-wrapper').find( '.summary' ).wrapInner('<div class="summary-inner-wrapper"></div>');

						    if (typeof(quickview_opt) != "undefined") {
							    $('.quick-view-wrapper').find( '.woocommerce-product-gallery' ).each( function() {
									$( this ).trigger( 'wc-product-gallery-before-init', [ this, quickview_opt ] );
									$( this ).wc_product_gallery( quickview_opt );
									$( this ).trigger( 'wc-product-gallery-after-init', [ this, quickview_opt ] );
								} );
							}

							$('.quick-view-wrapper').removeClass('loaded');

						    quickView.removeClass('loading');
							quickViewLoading   = false;

							ProductCount();

	                	} else {
	                		quickView.removeClass('loading');
							quickViewLoading   = false;
							console.log('No data');
						}
					},
					error: function(data){
						console.log('Something went wrong, please contact site administrator');
					}
	            });
			});

			$("body").on('click','.quick-view-wrapper-close, .quick-view-wrapper-after',function(e){

		    	var currentProduct = $('.qwc').find('.product').first().attr('id');

		    	var wish = $('.qwc').find('.wishlist-toggle.active');
		    	var comp = $('.qwc').find('.compare-toggle.active');

		    	$('.qwc').remove();

		    	$('#'+currentProduct).each(function(){
		    		if (wish.length) {
		    			$(this).find('.wishlist-toggle').addClass('active').attr('title',controller_opt.inWishlist);
		    			$(this).find('.wishlist-title').html(controller_opt.inWishlist);
		    		}
		    		if (comp.length) {
		    			$(this).find('.compare-toggle').addClass('active').attr('title',controller_opt.inCompare);
		    			$(this).find('.compare-title').html(controller_opt.inCompare);
		    		}
		    	});

		    	$('.sticky-dashboard').addClass('active');

		    	if (typeof(addToCart) != "undefined" && addToCart.length) {
					removeToCart.addClass('transform');
				}

		    });
		}

		function getPosts(postType,trigger,masonry){

			let dataMAX = trigger.attr('data-max'),
				dataNEXT = trigger.attr('data-next');

			let next = (postType == "product") ? controller_opt.productNextLink : controller_opt.postNextLink;

			if (typeof(dataNEXT) != "undefined" && dataNEXT != null) {
				next = dataNEXT;
			}

			if (typeof(dataMAX) != "undefined" && dataMAX != null) {
				max = dataMAX;
			}

			next = next.replace(/\/page\/[0-9]*/, '/page/'+ start);

			if(start <= max) {

				if (request) {
					return;
				}

				request = true;

				trigger.removeClass('disable').addClass('loading');

				$.get(next,function(content) {

					var content = $(content).find('#loop-'+postType+' > .post').addClass('append');

					if (typeof content !== "undefined") {

						start++;
						
						request = false;

						setTimeout(function(){
						
							$('#loop-'+postType).append(content);

							// plugins-recall

							if ($('#loop-posts').length) {

								if ($('.post-layout').hasClass('masonry')) {

									$('.masonry #loop-posts').masonry('destroy');
									$('.masonry #loop-posts').removeData('masonry');

									$('.masonry #loop-posts').masonry({
									  itemSelector: '.post',
									  columnWidth:'.post',
									  percentPosition:true,
									  gutter:0
									});

								}

								$('.post-media .slides').each(function(){
									var slider = tns({
										container: this,
										mode:'gallery',
										nav:false,
										items: 1
									});
								});

								videoTrigger();

								setTimeout(function(){
									$('.tns-controls-trigger button').on('click',function(){
										$('.tns-controls button[data-controls="'+$(this).attr('data-controls')+'"]').trigger('click');
									});

									$('.post-media .slides').each(function(){
										var lazyImage = $(this).find('li:last-child img.lazy');
										lazyImage.attr('src',lazyImage.data('src')).removeClass('lazy');
									});

								},200);

							}

							if ($('#loop-products').length) {
								quickView();
								ajaxAddToCart();
							}

							listImages();

							trigger.removeClass('loading');

							$('#loop-'+postType+' > .post').removeClass('append');

							lazyLoad(document.getElementById('loop-'+postType));

							if(start > max) {
								trigger.addClass("disable");
							}

						},1000);


					} else {
						alert('Something went wrong, please contact site administrator');
					}

				});

			}
		}

		function fetchPosts(postType){

			var loop    = $('#loop-'+postType),
				nav     = loop.data('nav'),
				trigger = $('.post-ajax-button');
			
			if(start > max) {
				trigger.addClass("disable");
			}

			trigger.on('click',function(e){
				e.preventDefault();
			});

			if (nav == "loadmore") {

				trigger = $('#loadmore');
				trigger.on('click',function(){

					var activeParams = getParams(),
						disable = (activeParams && activeParams['ajax'] == 'true') ? true : false;

					if (disable) {return;}

					trigger = $(this);
					getPosts(postType,trigger);
				});

			} else if(nav == "infinite"){

				trigger = $('#infinite');

				$(window).scroll(function(){

					var activeParams = getParams(),
						disable = (activeParams && activeParams['ajax'] == 'true') ? true : false;

					if (disable) {return;}

					if  (trigger.inView()){
						getPosts(postType,trigger);
					}
				});

			}
		}

		function filterPosts(postType,link,count,perPage,id,layout,full,loopId = ''){

			if (request) {
				return;
			}

			var trigger = $('#loop-'+postType+loopId).next('.post-ajax-button');

			request = true;

			$('#loop-'+postType+loopId).addClass('loading');
			
			trigger.removeClass('disable').addClass('loading');

			$.ajax({
                url:controller_opt.ajaxUrl,
                type: 'post',
                data: {
                	action:'term_filter',
                	id:id,
                	count:perPage,
                	layout:layout,
                	full:full
                },
                success: function(data) {
                	if (data.length) {

                		request = false;

                	 	start = parseInt(controller_opt.start) + 1;
						next  = link + '/page/' + start;
						max   = Math.ceil(count/perPage);

						setTimeout(function(){

							$('#loop-'+postType+loopId).html('');
							$('#loop-'+postType+loopId).append(data);

							// plugins-recall

							listImages();

							$('#loop-'+postType+loopId).removeClass('loading');
							trigger.removeClass("loading");

							$('#loop-'+postType+loopId+' > .post').removeClass('append');

							lazyLoad(document.getElementById('loop-'+postType+loopId));

							if(start > max) {
								trigger.addClass("disable");
							}

						},1000);

                	} else {
						alert('No data');
					}
				},
				error: function(data){
					alert('Something went wrong, please contact site administrator');
				}
            });

		}

		function validateValue($value, $target, $placeholder,$email,valid){
	        if ($email == true) {
	            if ($value == null || $value == "" || valid == "invalid") {
	                $target.addClass('visible');
	            } else {
	                $target.removeClass('visible');
	            }

	        } else {
	            if ($value == null || $value == "" || $value == $placeholder) {
	                $target.addClass('visible');
	            } else {
	                $target.removeClass('visible');
	            }
	        }
	    }

	    function productCarousel(products){

			var wooProducts = (products != null) ? '#'+products+'.swiper > .loop-products' : '.et-woo-products.swiper > .loop-products';

			$(wooProducts).each(function(){

				var $this       = $(this).addClass('enova-carousel'),
					scope       = this,
					autoplay    = $this.parents('.swiper-container').data('autoplay'),
					itemsmob    = 1.2,
					itemsmob320 = 1.2,
					items       = $this.parents('.swiper-container').data('columns'),
					items768    = $this.parents('.swiper-container').data('tab-port-columns'),
					items1024   = $this.parents('.swiper-container').data('tab-land-columns');

					if ($this.parent().hasClass('grid')) {
						itemsmob320 = 2.2;
						itemsmob    = 2.4;
						items768   += 0.4;
						items1024  += 0.4;
						if (items > 6) {items = 6}
					} else {
						items768  += 0.27;
						items1024 += 0.2;
						if (items > 4) {items = 4}
					}

				var config = {
					pagination: {
				        el: '#'+$this.parents('.swiper-container').find('.swiper-pagination').attr('id'),
				        clickable: true,
				        renderBullet: function (index, className) {
		          			return '<span class="' + className + '"></span>';
				        },
				    },
				    navigation: {
					    nextEl: '#'+$this.parents('.swiper-container').find('.swiper-button-next').attr('id'),
					    prevEl: '#'+$this.parents('.swiper-container').find('.swiper-button-prev').attr('id'),
					},
					spaceBetween: 16,
					slidesPerView: items,
					grabCursor: true,
					autoHeight: true,
					direction:'horizontal',
					loop: false,
					breakpoints: {
						200: {
							slidesPerView: itemsmob320,
							spaceBetween: 8,
						},
						375: {
							slidesPerView: itemsmob,
							spaceBetween: 8,
						},
						425: {
							slidesPerView: itemsmob,
							spaceBetween: 8,
						},
						540: {
							slidesPerView: 1.8,
							spaceBetween: 8,
						},
						768: {
							slidesPerView: items768,
							spaceBetween: 16,
						},
						1024: {
							slidesPerView: items1024,
							spaceBetween: 16
						},
						1280: {
							slidesPerView: items,
							spaceBetween: 16
						}
					}
				};

				if (typeof(autoplay) != "undefined" && autoplay == true) {
					config['autoplay'] = {
					    delay: 2000,
					    disableOnInteraction: false,
			    		pauseOnMouseEnter: true
					};

					config['loop'] = true;
				}

				var swiper = new Swiper('#'+$this.parent().attr('id'), config);

				if (typeof(autoplay) != "undefined" && autoplay == true) {
					swiper.on('slideChange', function () {
						lazyLoad(scope);
					});
				}

			});
		}

		function postCarousel(posts){

            var Posts = (posts != null) ? '#'+posts+'.swiper > .loop-posts' : '.et-posts.swiper > .loop-posts';

			$(Posts).each(function(){

				var $this       = jQuery(this).addClass('enova-carousel'),
					scope       = this,
					itemsmob    = ($this.parent().hasClass('list') || $this.parent().hasClass('full')) ? 1 : 1.6,
					itemsmob320 = ($this.parent().hasClass('list') || $this.parent().hasClass('full')) ? 1 : 1.4,
					items       = $this.parents('.swiper-container').data('columns'),
					items768    = $this.parents('.swiper-container').data('tab-port-columns'),
					items1024   = $this.parents('.swiper-container').data('tab-land-columns');

					if ($this.parent().hasClass('grid')) {
						items768  += 0.4;
						items1024 += 0.4;
					}

					if ($this.parent().hasClass('grid') && items > 4) {items = 4}
					if (($this.parent().hasClass('list') || $this.parent().hasClass('full')) && items > 2) {items = 2}

				var config = {
					pagination: {
				        el: '#'+$this.parents('.swiper-container').find('.swiper-pagination').attr('id'),
				        clickable: true,
				        renderBullet: function (index, className) {
		          			return '<span class="' + className + '"></span>';
				        },
				    },
				    navigation: {
					    nextEl: '#'+$this.parents('.swiper-container').find('.swiper-button-next').attr('id'),
					    prevEl: '#'+$this.parents('.swiper-container').find('.swiper-button-prev').attr('id'),
					},
					spaceBetween: 24,
					slidesPerView: items,
					grabCursor: true,
					autoHeight: true,
					direction:'horizontal',
					loop: false,
					breakpoints: {
						200: {
							slidesPerView: itemsmob320,
							spaceBetween: 8,
						},
						375: {
							slidesPerView: itemsmob,
							spaceBetween: 8,
						},
						425: {
							slidesPerView: itemsmob,
							spaceBetween: 8,
						},
						540: {
							slidesPerView: itemsmob,
							spaceBetween: 8,
						},
						768: {
							slidesPerView: items768,
						},
						1024: {
							slidesPerView: items1024,
						},
						1280: {
							slidesPerView: items,
						}
					}
				};

				if (typeof(autoplay) != "undefined" && autoplay == true) {
					config['autoplay'] = {
					    delay: 2000,
					    disableOnInteraction: false,
			    		pauseOnMouseEnter: true
					};
					config['loop'] = true;
				}

				var swiper = new Swiper('#'+$this.parent().attr('id'), config);

				if (typeof(autoplay) != "undefined" && autoplay == true) {
					swiper.on('slideChange', function () {
						lazyLoad(scope);
					});
				}

			});
        }

        function enovaCarousel(container){

        	var Carousel = (container != null) ? '#'+container+' .enova-carousel' : '.enova-carousel';


        	$(Carousel).each(function(){

        		if (!$(this).parent('.swiper-initialized').length) {

		   			var $scope = $(this),
		   				scope  = this,
						items     = $scope.find('.swiper-slide').length,
						desktop   = $scope.parents('.swiper-container').data('carousel-columns'),
	               		slider    = $scope.parents('.swiper-container').hasClass('slider') ? true : false,
						mobile    = $scope.parents('.swiper-container').data('carousel-mobile-columns'),
		 				tabletP   = $scope.parents('.swiper-container').data('carousel-tablet-portrait-columns'),
						tabletL   = $scope.parents('.swiper-container').data('carousel-tablet-landscape-columns'),
						gatter    = $scope.parents('.swiper-container').data('carousel-gatter'),
						autoplay  = $scope.parents('.swiper-container').data('carousel-autoplay'),
						loop      = $scope.parents('.swiper-container').data('carousel-loop'),
						navType   = $scope.parents('.swiper-container').data('carousel-navigation-type'),
						navPos    = $scope.parents('.swiper-container').data('carousel-navigation-position');

					if (typeof(loop) == 'undefined') {loop = false}

					desktop  = (typeof(desktop) == 'undefined') ? 3 : desktop;
					mobile   = (typeof(mobile) == 'undefined') ? 1 : mobile;
					tabletP  = (typeof(tabletP) == 'undefined') ? 2 : tabletP;
					tabletL  = (typeof(tabletL) == 'undefined') ? 3 : tabletL;
					gatter   = (typeof(gatter) == 'undefined') ? 0 : gatter;
					var gatterM  = gatter > 8 ? 8 : gatter;
					var gatterML = gatter > 12 ? 12 : gatter;
					autoplay = (typeof(autoplay) == 'undefined') ? false : autoplay;

					var config = {
						pagination: {
					        el: '#'+$scope.parents('.swiper-container').find('.swiper-pagination').attr('id'),
					        clickable: true,
					        renderBullet: function (index, className) {
			          			return '<span class="' + className + '"></span>';
					        },
					    },
					    navigation: {
						    nextEl: '#'+$scope.parents('.swiper-container').find('.swiper-button-next').attr('id'),
						    prevEl: '#'+$scope.parents('.swiper-container').find('.swiper-button-prev').attr('id'),
						},
						spaceBetween: gatter,
						slidesPerView: desktop,
						grabCursor: true,
						autoHeight: false,
						direction:'horizontal',
						breakpoints: {
							200: {
		                        slidesPerView: mobile + ((slider || mobile == items) ? 0 : 0.2),
		                        spaceBetween: gatterM,
		                    },
		                    375: {
		                        slidesPerView: mobile + ((slider || mobile == items) ? 0 : 0.3),
		                        spaceBetween: gatterM,
		                    },
		                    425: {
		                        slidesPerView: mobile + ((slider || mobile == items) ? 0 : 0.4),
		                        spaceBetween: gatterML,
		                    },
		                    540: {
		                        slidesPerView: mobile + ((slider || mobile == items) ? 0 : 0.6),
		                        spaceBetween: gatterML,
		                    },
		                    768: {
		                        slidesPerView: tabletP + ((slider || tabletP == items) ? 0 : 0.4),
		                        spaceBetween: gatter
		                    },
		                    1024: {
		                        slidesPerView: tabletL + ((slider || tabletL == items) ? 0 : 0.4),
		                        spaceBetween: gatter
		                    },
		                    1280: {
		                        slidesPerView: desktop,
		                        spaceBetween: gatter
		                    }
						}
					};

					if (typeof(autoplay) != "undefined" && autoplay == true) {
						config['autoplay'] = {
						    delay: 2000,
						    disableOnInteraction: false,
				    		pauseOnMouseEnter: true
						};
						config['loop'] = true;
					}

					var swiper = new Swiper('#'+$scope.parent('.swiper').attr('id'), config);

					if (typeof(autoplay) != "undefined" && autoplay == true) {
						swiper.on('slideChange', function () {
							lazyLoad(scope);
						});
					}

				}

	   		});
        }

		function etElements(){

			/* sidebar-menu
			----*/

				$('.sidebar-menu-container.accordion').each(function(){

					var $this = $(this);
					var childItems = $this.find('.menu-item-has-children > a');

					if ($this.find('.menu-item-has-children > a').attr( "href" ) == "#") {
						$this.find('.menu-item-has-children > a').unbind('click').on('click',function(e){
							if ($(this).next('ul').length != 0) {
								$(this).toggleClass('animate');
								$(this).next('ul').stop().slideToggle(200);
								$(this).parent().siblings().children('ul').slideUp(200);
								$(this).parent().siblings().children('a').removeClass('animate');
							};
							e.preventDefault();
						});
					} else {
						$this.find('.menu-item-has-children > a > span.toggle').unbind('click').on('click',function(e){
							e.stopImmediatePropagation();
							if ($(this).parent().next('ul').length != 0) {
								$(this).parent().toggleClass('animate');
								$(this).parent().next('ul').stop().slideToggle(200);
								$(this).parent().siblings().children('ul').slideUp(200);
							};
							e.preventDefault();
						});
					}

				});

			/* column-link
			----*/

				$('.has-link.elementor-column').each(function(){

					var target = (this.hasAttribute('data-link-target')) ? 'target="'+$(this).attr('data-link-target')+'"' : '';
					
					if($(this).find('.column-link').length){
						$(this).find('.column-link').attr('href',$(this).attr('data-link')).attr('target',target);
					} else {
						$(this).children('.elementor-widget-wrap').append('<a class="column-link" href="'+$(this).attr('data-link')+'" '+target+'></a>');
					}
					
					
				});

			/* et-button
			----*/

				$('.et-button').each(function(){

					var $this  = $(this),
						effect = $this.data('effect');

					if (effect == 'scale') {
						var tl = new gsap.timeline({paused: true});
						var back = $this.find('.button-back');

						$this.on('mouseover',function(){
							gsap.to(back,0.8, {
								scale:1.05,
								ease:"elastic.out"
							});
						});

						$this.on('mouseout',function(){
							gsap.to(back,0.8, {
								scale:1,
								ease:"expo.out"
							});
						});
					}


					if ($this.hasClass('click-smooth') && $this.hasClass('modal-false')) {
						$this.unbind('click').on('click',function(){
							gsap.to(window, {
								duration: 1, 
								scrollTo: {y:$this.attr('href')},
								ease:Power3.easeOut 
							});
							return false;
						});
					}

					if (!$this.hasClass('click-smooth') && $this.hasClass('modal-true')) {
						$this.unbind('click').on('click',function(e){
							e.preventDefault();
							gsapLightbox($(this),false);
						});
					}

				});

				$('.et-button.submenu-toggle-click').each(function(){
					if ($(this).next('.sub-menu').length) {
						$(this).unbind('click').on('click',function(e){
							e.preventDefault();
							$(this).removeClass('loading-menu').toggleClass('active');

							if ($(this).parents('.header').length && $(this).hasClass('active')) {
								jQuery('.header .hbe-toggle.active').not('.mobile-toggle').each(function(){
									jQuery(this).parent().find('.hbe-toggle').trigger('click');
								});
								jQuery('.footer .hbe-toggle.active').not('.mobile-toggle').each(function(){
									jQuery(this).parent().find('.hbe-toggle').trigger('click');
								});
							}

						});
					}
				});

				$('.et-button.submenu-toggle-hover').each(function(){

					var $this = $(this);

					if ($this.next('.sub-menu').length) {
						$this.removeClass('loading-menu');
					}

					$this.unbind('mouseenter').on('mouseenter',function(){
						if (!$this.next('.sub-menu').length) {
							$this.addClass('loading-menu');
						} else {
							$this.removeClass('loading-menu');
						}
					});

					$this.parent().hover(
						function(){
							setTimeout(function(){$this.parent().addClass('hover');},200);
						},
						function(){
							$this.parent().removeClass('hover');
						}
					);

				});

			/* et-heading
			----*/

				$('.et-heading.animate-true').each(function(){

					var $this = $(this),
						delay = '+='+(0.2 + parseInt($this.data('delay'))/1000),
						text  = $this.find('.text');

					if(!$this.hasClass('fired')){

						if (!$this.hasClass('timeline')) {

							var tl = new gsap.timeline({paused: true});

							if ($this.hasClass('curtain')) {

								var curtain = $this.find('.curtain');

								tl.to(curtain,0.8, {
								  scaleX:1,
								  transformOrigin:'left top',
								  ease:"power3.out"
							    },delay);

							    tl.to(curtain,0.8, {
								  scaleX:0,
								  transformOrigin:'right top',
								  ease:"power3.out"
							    });

							    tl.to(text,0.2, {
								  opacity:1,
							    },'-=0.8');
							}

							else if ($this.hasClass('letter')) {
								var letterText = new SplitText($this.find('.text'),{type:"chars"});

								gsap.set($this,{perspective:500});

								tl.from(letterText.chars,{
									duration: 0.2,
								},delay);

								tl.from(letterText.chars,{
									duration: 0.6,
									opacity:0,
									scale:3,
									x:100,
									y:50,
									force3D:true,
									stagger: 0.01,
									ease:"expo.out"
								},'-=0.2');

							}

							else if ($this.hasClass('words')) {

								var wordsText = new SplitText($this.find('.text'),{type:"words"});
								
								gsap.set($this,{perspective:500});

								tl.from(wordsText.words,{
									duration: 0.2,
								},delay);

								tl.from(wordsText.words,{
									duration: 0.8,
									opacity:0,
									scaleY:1.5,
									transformOrigin:'left top',
									y:24,
									force3D:true,
									stagger: 0.04,
									ease:"expo.out"
								},'-=0.2');

							}

							else if ($this.hasClass('rows')) {
								
								var rowsText = new SplitText($this.find('.text'),{type:"lines"});
								
								gsap.set($this,{perspective:1000});

								tl.from(rowsText.lines,{
									duration: 0.4,
								},delay);

								tl.from(rowsText.lines,{
									duration: 1.2,
									opacity:0,
									rotationX:8,
									rotationY:-50,
									rotationZ:8,
									y:50,
									x:-50,
									z:50,
									transformOrigin:'left top',
									force3D:true,
									stagger: 0.08,
									ease:"expo.out"
								},'-=0.2');

							}

							$this.addClass('timeline');

							setTimeout(function(){

								$this.waypoint({
					                handler: function(direction) {

					                	tl.progress(0);
										tl.play();

					                    this.destroy();

					                    $this.addClass('fired');

					                },
					                offset: 'bottom-in-view'
					            });

				            },1);

						}

					}

				});

			/* et-accordion
			----*/
		
				$('.et-accordion').each(function(){

					var $this = $(this);

					gsap.set($this.find('.accordion-title.active').next(),{
	    				height: 'auto'
					});


					$this.find('.accordion-title').unbind('click').on('click', function(e){

						e.stopPropagation();

						var $self = $(this);

							if(!$self.hasClass('active')){
								if($this.hasClass('collapsible-true')){

									$self.addClass("active").siblings().removeClass("active");

									gsap.to($self.next(),0.2, {
										height:'auto',
										ease:"expo.out"
								  	});

									gsap.to($this.find('.accordion-content').not($self.next()),0.2, {
										height:0,
										ease:"expo.out"
								  	});

								} else {
									$self.addClass("active");

									gsap.to($self.next(),0.2, {
										height:'auto',
										ease:"expo.out"
								  	});

								}
							} else {
								if(!$this.hasClass('collapsible-true')){
									$self.removeClass("active");
									$self.removeClass("active");

									gsap.to($self.next(),0.2, {
										height:0,
										ease:"expo.out"
								  	});

								}
							}

					});

					

				});

			/* et-tabs
			----*/

				$('.et-tabs').each(function(){

					var $this    = $(this),
						tabs     = $this.find('.tab'),
						tabsQ    = tabs.length,
						tabsDefaultWidth  = 0,
						tabsDefaultHeight = 0,
						tabsContent = $this.find('.tab-content');
						
						if(!tabs.hasClass('active')){
							tabs.first().addClass('active');
						}

						tabs.each(function(){

							var $thiz = $(this);

							if ($thiz.hasClass('active')) {
								$thiz.siblings().removeClass("active");
								tabsContent.eq($thiz.index()).addClass('active').siblings().removeClass('active');
							}

						});

						if(tabsQ >= 2){

							tabs.unbind('click').on('click', function(){
								var $self = $(this);
								
								if(!$self.hasClass("active")){

									$self.addClass("active");

									$self.siblings()
									.removeClass("active");

									tabsContent.removeClass('active');
									tabsContent.eq($self.index()).addClass('active');
								}
								
							});
						}

						if(tabsDefaultWidth >= $this.outerWidth()  && $this.hasClass('horizontal')){
			                $this.addClass('tab-full');
			            } else {
			                $this.removeClass('tab-full');
			            }


				});

			/* et-animate-box
			----*/

				$('.et-animate-box').each(function(){

					var element   = this,
						$this     = $(element),
						id        = $this.attr('id'),
						delay     = '+='+(0.2 + parseInt($this.data('delay'))/1000),
						animation = $this.data('animation'),
						offset    = (animation == 'bottom') ? '100%': '70%',
						stagger   = $this.data('stagger'),
						content   = $this.find('.content').children();

					if(!$this.hasClass('fired')){

						animateBoxBack(element);

						var tl = new gsap.timeline({paused: true});

						buildAnimateBoxTimeline(tl,$this,delay,animation,stagger,content);

						setTimeout(function(){

							$this.waypoint({
				                handler: function(direction) {

				                	$this.addClass('active');

				                	tl.progress(0);
									tl.play();

				                    this.destroy();

				                    $this.addClass('fired');

				                },
				                offset: offset
				            });

			            },1);

			            $(window).resize(function(){

			            	setTimeout(function(){

				            	element = document.getElementById(id);

				            	$this = $('#'+id);

				            	animateBoxBack(element);

				            	if (!$this.hasClass('active')) {

					            	var startC = $this.find('.box-back path').attr('data-dclone');
									$this.find('.box-back path').attr('d',startC);

					            	tl.seek('end').kill();

					            	tl = new gsap.timeline({paused: true});

					            	buildAnimateBoxTimeline(tl,$this,delay,animation,stagger,content);

					            	setTimeout(function(){

						            	$this.waypoint({
							                handler: function(direction) {

							                	tl.progress(0);
												tl.play();

							                    this.destroy();

							                },
							                offset: offset
							            });

						            },1);

					            }

				            },50);

						});

		        }

				});

			/* et-stagger-box
			----*/

				$('.et-stagger-box').each(function(){

					var element   = this,
						$this     = $(element),
						id        = $this.attr('id'),
						delay     = '+='+(0.2 + parseInt($this.data('delay'))/1000),
						interval  = parseInt($this.data('interval'))/1000,
						stagger   = $this.data('stagger'),
						content   = $this.children('.e-con-inner').length ? 
						$this.children('.e-con-inner').children('.elementor-element').not('.elementor-widget-et_gap') : 
						$this.children('.elementor-element').not('.elementor-widget-et_gap');

					if(!$this.hasClass('fired')){

						if (!$this.hasClass('stagger-active')) {
							var tl = new gsap.timeline({paused: true});
							buildStaggerBoxTimeline(tl,delay,interval,stagger,content);
							$this.addClass('stagger-active');

							setTimeout(function(){

								$this.waypoint({
									handler: function(direction) {
										
										$this.addClass('active');

										tl.progress(0);
										tl.play();

										this.destroy();

										$this.addClass('fired');

									},
									offset: '70%'
								});

							},1);

						}

					}

				});

			/* et-content-box
			----*/

				$('.et-icon-box.transform').each(function(){
					$(this).parent().addClass('et-icon-box-transform');
				});

			/* et-image
			----*/

				if ($(window).width() > 1200) {

					$('.revslider-initialised')
					.on('mousemove',function(e){
						$('.parallax-on-move img').each(function(){
							var amountMovedX = (e.pageX * -1 / 100);
						    var amountMovedY = (e.pageY * -1 / 100);
						    $(this).css('transform', 'translate('+amountMovedX + 'px,' + amountMovedY + 'px)');
						});
					})
					.on('mouseleave',function(e){
						$('.parallax-on-move[data-initialised="true"] img').each(function(){
						    $(this).css('transform', 'translate(0px,0px)');
						});
					});

				} else {
					$('.parallax-on-move[data-initialised="true"] img').each(function(){
					    $(this).css('transform', 'translate(0px,0px)');
					});
				}

				$('.et-image.parallax').each(function(){

					var $this = $(this);
					var x     = $this.data('coordinatex'),
                        y     = $this.data('coordinatey'),
                        limit = $this.data('limit');

                    if (typeof(limit) == 'undefined') {limit = 0}

					$(window).scroll(function(){

						if (!$this.hasClass('parallax-off')) {

							var yPos   = Math.round((0-$(window).scrollTop()) / $this.data('speed'))  +  y;
							var scroll = (Math.sign(y) == -1) ? Math.round((0-$(window).scrollTop()) / $this.data('speed')) : yPos;

							if (Math.abs(scroll) > limit && limit > 0) {
								yPos = (Math.sign(y) == -1) ? Math.sign(yPos)*(limit+Math.abs(y)) : Math.sign(yPos)*limit;
							}

							gsap.to($this,0.8,{
								x:x,
								y:yPos,
								force3D:true,
							});

						}

					});
					
				});

				disableParallax();	
				$(window).resize(disableParallax);

			/* et-gallery
			----*/

				$('.et-gallery').each(function(){

					var $this = $(this);

					if ($this.hasClass('slider')) {

						var lazyImage = $this.find('ul .et-gallery-item:last-child img.lazy');

						lazyImage.attr('src',lazyImage.data('src')).removeClass('lazy');
						lazyImage.parent().addClass('loaded');

					}

				});

			/* et-carousel
			----*/

				enovaCarousel();
				productCarousel();
				postCarousel();

			/* mailchimp
			----*/

			    $('.et-mailchimp-form').each(function(){

			        var valid = "invalid";
			        var $this = $(this);

			        $this.unbind('submit').submit(function(event) {

			            event.preventDefault();

			            var formData = $this.serialize();

			            var email   = $this.find("input[name='email']"),
			                fname   = $this.find("input[name='fname']"),
			                list    = $this.find("input[name='list']");


			            var emailValue = email.val();
			            var n = emailValue.indexOf("@");
			            var r = emailValue.lastIndexOf(".");
			            if (n < 1 || r < n + 2 || r + 2 >= emailValue.length) {
			                valid =  "invalid";
			            } else {
			                valid = "valid";
			            }

			            validateValue(email.val(), email.next(".alert"), email.attr('data-placeholder'), true, valid);

			            if (fname.length && fname.attr('data-required') == "true") {validateValue(fname.val(), fname.next(".alert"), fname.attr('data-placeholder'), false);}

			            if (email.val() != email.attr('data-placeholder') && valid == "valid"){

			                if(fname.length && fname.attr('data-required') == "true" && fname.val() == fname.attr('data-placeholder')){event.preventDefault();}

			                $this.find(".sending").addClass('visible');

			                $.ajax({
			                    type: 'POST',
			                    url: $this.attr('action'),
			                    data: formData
			                })
			                .done(function(response) {

			                	console.log(response);

			                    $this.find(".sending").removeClass('visible');
			                    $this.find(".et-mailchimp-success").addClass('visible');
			                    setTimeout(function(){
			                        $this.find(".et-mailchimp-success").removeClass('visible');
			                    },2000);
			                })
			                .fail(function(data) {

			                	console.log(response);
			                	
			                	
			                    $this.find(".sending").removeClass('visible');
			                    $this.find(".et-mailchimp-error").addClass('visible');
			                    setTimeout(function(){
			                        $this.find(".et-mailchimp-error").removeClass('visible');
			                    },2000);
			                })
			                .always(function(){
			                    setTimeout(function(){
			                        // Clear the form.
			                        $this.find("input[name='email']").val(email.attr('data-placeholder'));
			                        $this.find("input[name='fname']").val(fname.attr('data-placeholder'));
			                    },2000);
			                });

			            }
			        });

			        $this.find('input').on('focus',function(){
			            $(this).next('.visible').removeClass('visible');
			        });
			        
			    });

			/* et-counter
			----*/

				$('.et-counter').each(function(){

					var $this    = $(this),
						dDelay   = $this.data('delay'),
						delay    = (dDelay) ? dDelay/1000 : (0.2 + $this.index()*0.01),
						value    = $this.data('value'),
						counterV = { var: 0 },
						counter  = $this.find('.counter');

					if (!$this.hasClass('fired')) {

						var tl = new gsap.timeline({paused: true});

						tl.to($this.find('.in'),{
							duration: 0.8,
							delay:delay,
							opacity:1,
							stagger: 0.1,
							x:0,
							transformOrigin:'left top',
							force3D:true,
							ease:"expo.out"
						});


						tl.to(counterV,{
							var:value,
							duration:1,
							onUpdate: function () {
						        counter.html(Math.ceil(counterV.var));
		                    },
						},'-=0.85');

						tl.to($this.find('.icon'),{
							duration: 0.2,
							opacity:1,
						},'-=0.6');

						tl.to($this.find('.icon'),{
							duration: 1.6,
							scale:1,
							force3D:true,
							ease:"elastic.out"
						},'-=0.6');

						setTimeout(function(){

							$this.waypoint({
				                handler: function(direction) {

				                	$this.addClass('active');

				                	tl.progress(0);
									tl.play();

				                    this.destroy();

				                    $this.addClass('fired');

				                },
				                offset: 'bottom-in-view'
				            });

			            },1);

		            }


				});

			/* et-progress
			----*/

				$('.et-progress').each(function(){

					var $this    = $(this),
						type     = ($this.hasClass('circle')) ? 'circle' : 'default',
						delay    = (0.2 + $this.index()*0.01),
						value    = $this.data('percentage'),
						counterV = { var: 0 },
						counter  = $this.find('.percent');

					if (!$this.hasClass('fired')) {

						if (!$this.hasClass('timeline')) {

							var tl = new gsap.timeline({paused: true});

							if (type == 'default') {

								var transformOrigin = isRTL ? 'right top' : 'left top';

								tl.from($this.find('.bar'),{
				                    duration: 1.6,
				                    delay:delay,
				                    scaleX:0,
				                    force3D:true,
				                    transformOrigin:transformOrigin,
				                    ease:"expo.out"
				                });

				                tl.from($this.find('.text'),{
				                    duration: 0.8,
				                    opacity:0,
				                    x:50,
				                    transformOrigin:transformOrigin,
				                    force3D:true,
				                    ease:"expo.out"
				                },'-=1.6');

				                tl.to(counterV,{
				                    var:value,
				                    duration:1,
				                    onUpdate: function () {
				                        $this.find('.bar').html('<span class="percent">'+Math.ceil(counterV.var)+'</span>');
				                    },
				                },'-=1.4');

							} else {

								var bar           = this.querySelector('.bar-circle'),
									circumference = 27 * 2 * Math.PI,
									offset        = circumference - value / 100 * circumference;

								bar.style.strokeDasharray = circumference+' '+circumference;
								bar.style.strokeDashoffset = circumference;

								tl.to(bar,{
									duration: 0.2,
									delay:delay,
									opacity:1
								});

								tl.to(bar,{
									duration: 2,
									strokeDashoffset:offset,
									ease:"expo.out"
								},'-=0.2');

								tl.from($this.find('.text').children(),{
									duration: 0.8,
									opacity:0,
									y:50,
									stagger:0.1,
									transformOrigin:'left top',
									force3D:true,
									ease:"expo.out"
								},'-=2');

								tl.to(counterV,{
									var:value,
									duration:1,
									onUpdate: function () {
								        counter.html(Math.ceil(counterV.var));
				                    },
								},'-=2');

							}

							$this.addClass('timeline');

							setTimeout(function(){

								$this.waypoint({
					                handler: function(direction) {

					                	$this.addClass('active');

					                	tl.progress(0);
										tl.play();

					                    this.destroy();

					                    $this.addClass('fired');

					                },
					                offset: 'bottom-in-view'
					            });

				            },1);

						}
					}

				});

			/* et-timer
			----*/

				$('.et-timer').each(function(){

					var $this   = $(this),
						extend  = $this.data('number'),
						enddate = $this.data('enddate'),
						gmt     = $this.data('gmt'),
						reset   = (typeof(extend) != 'undefined' && extend != null) ? true : false,
						gmt     = (typeof(gmt) != 'undefined' && gmt != null) ? gmt : 0;

					if (!$this.hasClass('fired')) {

						var today   = new Date();
						var enddate = new Date(enddate);

						if (reset && today >= enddate) {
							enddate = new Date();
	  						enddate.setDate(enddate.getDate() + extend);
						}

			            $this.find('ul').countdown({
			                date: enddate,
			                offset: $this.data('gmt'),
			            });

			            $this.addClass('fired');

		            }

				});
				
		}

		function containerExtended(){
			$('.et-popup-banner').each(function(){

				var $this  = $(this);
				var	$delay = $this.attr('data-popup-delay');
				var cookie = $this.attr('data-popup-cookie');

				$this.wrap('<div class="et-popup-banner-wrapper"></div>');
				$this.prepend('<div class="popup-banner-toggle"></div>');

				if ($this.hasClass('elementor-hidden-desktop')) {
					$this.parent().addClass('elementor-hidden-desktop');
				}

				if ($this.hasClass('elementor-hidden-tablet')) {
					$this.parent().addClass('elementor-hidden-tablet');
				}

				if ($this.hasClass('elementor-hidden-mobile')) {
					$this.parent().addClass('elementor-hidden-mobile');
				}

				var play = false;

				if(typeof(cookie) == 'undefined'){
					play = true;
					$.removeCookie($this.attr('data-id'), { path: '/' });
				} else
				if ((cookie == 'true' && typeof($.cookie($this.attr('data-id'))) == 'undefined' && $.cookie($this.attr('data-id')) != null)) {
					play = true;
				} else {
					$.removeCookie($this.attr('data-id'), { path: '/' });
				}

				if (play) {

					setTimeout(function(){
						$this.parent().addClass('animate');
					},$delay);

					$this.find('.popup-banner-toggle').bind('click',function(){
						$this.parent().removeClass('animate');
						if (cookie == 'true') {
							$.cookie($this.attr('data-id'),'active',{ expires: 1,path: '/'});
						}
					});

				}

			});

			$('.et-toggle-banner').each(function(){

				var $this  = $(this);
				var cookie = $this.attr('data-cookie');

				$this.wrap('<div class="et-toggle-banner-wrapper"></div>');

				if (!$this.find('.toggle-banner-toggle').length) {
					$this.prepend('<div class="toggle-banner-toggle"></div>');
				}

				if ($this.hasClass('elementor-hidden-desktop')) {
					$this.parent().addClass('elementor-hidden-desktop');
				}

				if ($this.hasClass('elementor-hidden-tablet')) {
					$this.parent().addClass('elementor-hidden-tablet');
				}

				if ($this.hasClass('elementor-hidden-mobile')) {
					$this.parent().addClass('elementor-hidden-mobile');
				}

				var play = false;

				if(typeof(cookie) == 'undefined'){
					play = true;
					$.removeCookie($this.attr('data-id'), { path: '/' });
				} else
				if ((cookie == 'true' && typeof($.cookie($this.attr('data-id'))) == 'undefined' && $.cookie($this.attr('data-id')) != null)) {
					play = true;
				} else {
					$.removeCookie($this.attr('data-id'), { path: '/' });
				}

				if (play) {

					$this.parent().addClass('animate');
					
					$this.find('.toggle-banner-toggle').bind('click',function(){
						$(this).addClass('hide');
						$this.parent().slideUp(300);
						if (cookie == 'true') {
							$.cookie($this.attr('id'),'active',{ expires: 1,path: '/'});
						}
					});

				}

			});

			$('.section-tab').each(function(){

	        	var $scope = $(this);
				var $children  = $scope.children('.e-con-inner').length ? $scope.children('.e-con-inner').children('.e-con') : $scope.children('.e-con');

				if (typeof($children) != "undefined") {

		        	var tabset = '<div class="tabset section-tabset section-tabs-component">';

		        		$children.wrapAll('<div class="section-tabs-container tabs-container section-tabs-component" />');

						$children.each(function(){

							var tab    = $(this).addClass('section-tab-item').addClass('tab-content'),
								title  = ((typeof(tab.attr('data-section-tab-title')) != 'undefined') ? tab.attr('data-section-tab-title') : 'Tab title #'+(tab.index()+1)),
								icon   = tab.attr('data-section-tab-icon'),
								active = tab.hasClass('active');

							tabset += (active) ? '<div class="tab section-tab-item active">' : '<div class="tab section-tab-item">';
								if (typeof(icon) != "undefined" && icon.length) {
									tabset += '<span class="icon section-tab-icon" style="mask: url('+icon+') no-repeat 50% 50%;-webkit-mask: url('+icon+') no-repeat 50% 50%;margin-right: 8px;width: 20px;height: 20px;"></span>';
								}
								if (typeof(title) != "undefined" && title.length) {
									tabset += '<span class="txt">'+title+'</span>';
								}
							tabset += '</div>';
						});

						tabset += '</div>';

						$(tabset).insertBefore($scope.find('.section-tabs-container'));

						$scope.find('.section-tabs-component').wrapAll('<div class="section-tab '+$scope.data('section-tabs-type')+'" />');

					var tabs 	          = $scope.find('.tab'),
						tabsQ    		  = tabs.length,
						tabsDefaultWidth  = 0,
						tabsDefaultHeight = 0,
						tabsContent 	  = $scope.find('.section-tabs-container').children('.tab-content'),
						action      	  = 'click';

					var tabSet = $scope.find('.tabset');

					if(!tabs.hasClass('active')){
						tabs.first().addClass('active');
					}

					tabs.each(function(){

						var $thiz = $(this);

						if ($thiz.hasClass('active')) {
							$thiz.siblings().removeClass("active");
							tabsContent.eq($thiz.index()).addClass('active').siblings().removeClass('active');
						}

					});

					if(tabsQ >= 2){

						tabs.on('click', function(event){
							event.stopImmediatePropagation();

							var $self = jQuery(this);

							if(!$self.hasClass("active")){

								$self.addClass("active");

								$self.siblings()
								.removeClass("active");

								tabsContent.removeClass('active');
								tabsContent.eq($self.index()).addClass('active');
								
							}
						});
						
					}

				}

			});

			$('.section-accordion').each(function(){

	        	var $scope    = $(this);
				var $children = $scope.children('.e-con-inner').length ? $scope.children('.e-con-inner').children('.e-con') : $scope.children('.e-con');

	        	if (typeof($children) != "undefined") {

			    		var sectionAccordionHTML = $scope[0].hasAttribute('data-section-accordion-type') ? 
			    		'<div class="section-accordion collapsible-'+$scope.data('section-accordion-type')+'"/>' :
			    		'<div class="section-accordion" />';

			    		$children.wrapAll(sectionAccordionHTML);

			    		$children.each(function(){

							var accordion = jQuery(this).addClass('section-accordion-content').addClass('section-accordion-item'),
								title     = ((typeof(accordion.attr('data-section-accordion-title')) != 'undefined') ? accordion.attr('data-section-accordion-title') : 'Accordion title #'+(accordion.index()+1)),
								icon      = accordion.attr('data-section-accordion-icon'),
								active    = accordion.hasClass('active');

							var acTitle = (active) ? '<div class="accordion-title section-accordion-title active">' : '<div class="accordion-title section-accordion-title">';
								if (typeof(icon) != "undefined" && icon.length) {
									acTitle += '<span class="accordion-icon section-accordion-icon" style="mask: url('+icon+') no-repeat 50% 50%;-webkit-mask: url('+icon+') no-repeat 50% 50%;margin-right: 8px;width: 20px;height: 20px;"></span>';
								}
								if (typeof(title) != "undefined" && title.length) {
									acTitle += '<span class="txt">'+title+'</span>';
								}
							acTitle += '</div>';

							jQuery(acTitle).insertBefore(accordion);
						});
			    	}

	        	gsap.set($scope.find('.section-accordion-title.active').next(),{
					opacity: 1,
    				height: 'auto'
				});

				$scope.find('.section-accordion-title').unbind('click').on('click', function(e){

					e.stopPropagation();

					var $self = $(this);

						if(!$self.hasClass('active')){
							if($scope.hasClass('collapsible-true')){

								$self.addClass("active").siblings().removeClass("active");

								gsap.to($self.next(),0.6, {
									height:'auto',
									ease:"expo.out"
							  	});

							  	gsap.to($self.next(),0.2, {
									opacity:1,
							  	});

							  	gsap.to($scope.find('.section-accordion-content').not($self.next()),0.1, {
									opacity:0,
							  	});

								gsap.to($scope.find('.section-accordion-content').not($self.next()),0.6, {
									height:0,
									ease:"expo.out"
							  	});

							} else {
								$self.addClass("active");

								gsap.to($self.next(),0.6, {
									height:'auto',
									ease:"expo.out"
							  	});

							  	gsap.to($self.next(),0.2, {
									opacity:1,
							  	});

							}
						} else {
							if(!$scope.hasClass('collapsible-true')){
								$self.removeClass("active");
								$self.removeClass("active");

								gsap.to($self.next(),0.1, {
									opacity:0,
							  	});

								gsap.to($self.next(),0.6, {
									height:0,
									ease:"expo.out"
							  	});
							}
						}

				});

			});

			$('.section-carousel').each(function(){

	        	var $scope = $(this);
	        	var scope = this;
				var $children = $scope.children('.e-con-inner').length ? $scope.children('.e-con-inner').children('.e-con') : $scope.children('.e-con');

				if (typeof($children) != "undefined") {

					var id        = $scope.data('id'),
						items     = $children.length,
						desktop   = $scope.data('carousel-columns'),
						mobile    = $scope.data('carousel-mobile-columns'),
		 				tabletP   = $scope.data('carousel-tablet-portrait-columns'),
						tabletL   = $scope.data('carousel-tablet-landscape-columns'),
						gatter    = $scope.data('carousel-gatter'),
						autoplay  = $scope.data('carousel-autoplay'),
						loop      = $scope.data('carousel-loop'),
						navType   = $scope.data('carousel-navigation-type'),
						navPos    = $scope.data('carousel-navigation-position');

					desktop  = (typeof(desktop) == 'undefined') ? 4 : desktop;
					mobile   = (typeof(mobile) == 'undefined') ? 1 : mobile;
					tabletP  = (typeof(tabletP) == 'undefined') ? 2 : tabletP;
					tabletL  = (typeof(tabletL) == 'undefined') ? 3 : tabletL;
					gatter   = (typeof(gatter) == 'undefined') ? 0 : gatter;
					var gatterM  = gatter > 8 ? 8 : gatter;
					autoplay = (typeof(autoplay) == 'undefined') ? false : autoplay;

					$children
					.addClass('swiper-slide')
					.wrapAll('<div class="swiper-wrapper enova-carousel" />');

					$children.parent('.swiper-wrapper').wrap('<div id="swiper-'+id+'" class="swiper container-swiper" />');
					$children.parents('.swiper').wrap('<div class="swiper-container" data-navigation-type="'+navType+'" data-arrows-pos="'+navPos+'" />');

					$scope.find('.swiper-container').append('<div id="prev-'+id+'" class="swiper-button container-swiper-nav swiper-button-prev"></div><div id="next-'+id+'" class="swiper-button container-swiper-nav swiper-button-next"></div><div id="swiper-pagination-'+id+'" class="swiper-pagination container-swiper-nav"></div>');

					var config = {
						pagination: {
					        el: '#'+$scope.find('.swiper-pagination').attr('id'),
					        clickable: true,
					        renderBullet: function (index, className) {
			          			return '<span class="' + className + '"></span>';
					        },
					    },
					    navigation: {
						    nextEl: '#'+$scope.find('.swiper-button-next').attr('id'),
						    prevEl: '#'+$scope.find('.swiper-button-prev').attr('id'),
						},
						spaceBetween: gatter,
						slidesPerView: desktop,
						grabCursor: true,
						autoHeight: false,
						direction:'horizontal',
						breakpoints: {
							200: {
								slidesPerView: mobile + ((items == mobile) ? 0 : 0.2),
								spaceBetween: gatterM,
							},
							375: {
								slidesPerView: mobile + ((items == mobile) ? 0 : 0.3),
								spaceBetween: gatterM,
							},
							425: {
								slidesPerView: mobile + ((items == mobile) ? 0 : 0.4),
								spaceBetween: gatterM,
							},
							540: {
								slidesPerView: mobile + ((items == mobile) ? 0 : 0.6),
								spaceBetween: gatterM,
							},
							768: {
								slidesPerView: tabletP + ((items == tabletP) ? 0 : 0.4),
								spaceBetween: gatter
							},
							1024: {
								slidesPerView: tabletL + ((items == tabletL) ? 0 : 0.4),
								spaceBetween: gatter
							},
							1280: {
								slidesPerView: desktop,
								spaceBetween: gatter
							}
						}
					};

					if (typeof(autoplay) != "undefined" && autoplay == true) {
						config['autoplay'] = {
						    delay: 2000,
						    disableOnInteraction: false,
				    		pauseOnMouseEnter: true
						};

						config['loop'] = true;

					}

					var swiper = new Swiper('#swiper-'+id, config);

					if (typeof(autoplay) != "undefined" && autoplay == true) {
						swiper.on('slideChange', function () {
							lazyLoad(scope);
						});
					}

				}

			});

			$('.et-parallax').each(function(){
	            var $this = $(this);
				
	            $this.append('<div class="parallax-container active" style="background-image:url('+$this.attr('data-parallax-image')+');" />');

	            var plx      = $this.find('.parallax-container'),
					duration = parseInt($this.data('parallax-duration')),
	            	ratio    = (typeof(duration) != 'undefined' && duration != null && duration != 0) ? 0.5 : 1;

            	if (duration == null) {duration = 0;}

            	duration = duration/100;

	            $(window).scroll(function() {
	                var yPos = Math.round(($(window).scrollTop()-plx.offset().top));

	                yPos = ratio*yPos;

	                gsap.to(plx,{
	                	duration:duration,
	                	delay:0,
	                	y:yPos,
	            	});
	            });

	        });
		}

		function afterProductsFetch(id = false){
			ajaxAddToCart();
			listImages();
			if (id) {
				lazyLoad(document.getElementById(id));
				productCarousel(id);
				enovaCarousel(id);
			}
			quickView();
		}

		function afterPostFetch(id = false){
			listImages();
			if (id) {
				lazyLoad(document.getElementById(id));
				postCarousel(id);
				videoTrigger();
			}
		}

		function productLoad(){

			let products = [].slice.call(document.querySelectorAll(".ajax.only.et-woo-products"));
		    if (typeof(products) != 'undefined' && products.length) {

		    	var ajaxCalls = [];
		    	var queryID   = '';
		    	
		    	products.forEach(function(item, index) {
					let woo   = item,
						id    = woo.getAttribute('id'),
						atts  = woo.parentNode.getAttribute('data-atts'),
						query = woo.parentNode.getAttribute('data-query'),
						args  = [];

					args.push(id);
					args.push(atts);
					args.push(query);

					queryID+=id.replace('et-woo-products-','');

					ajaxCalls.push(args.join('|'));

				});

				var args = {};

				args['action']   = 'woo_products_ajax';
				args['ajax']     = 'true';
				args['currency'] = controller_opt.currency;
				if (ajaxCalls.length) {
					args['ajax_calls'] = ajaxCalls.join(",");
				}

				jQuery.ajax({
		            url:controller_opt.ajaxUrl,
		            type: 'post',
		            data: args,
		            success: function(output) {
		            	output = JSON.parse(output);
		            	Object.entries(output).forEach(entry => {
						    const [key, value] = entry;
						    jQuery('#'+key).parent().replaceWith(value);
		                	lazyLoad(document.getElementById(key));
							productCarousel(key);
							enovaCarousel(key);
						});
						afterProductsFetch();
		            },
		            error:function () {
		                console.log(controller_opt.wooError);
		            }
		        });

		    }

		}

		function postLoad(){

			let posts = [].slice.call(document.querySelectorAll(".ajax.et-shortcode-posts"));

			if (typeof(posts) != 'undefined' && posts.length) {

				var ajaxCalls = [];
				var queryID   = '';

		    	posts.forEach(function(item, index) {
					let postList   = item,
						id         = postList.getAttribute('id'),
						atts       = postList.parentNode.getAttribute('data-atts'),
						query      = postList.parentNode.getAttribute('data-query'),
						args       = [];

					args.push(id);
					args.push(atts);
					args.push(query);

					ajaxCalls.push(args.join('|'));

					queryID+=id.replace('et-posts-','');

				});

				var args = {};

				args['action']   = 'et_posts_ajax';
				args['ajax']     = 'true';
				if (ajaxCalls.length) {
					args['ajax_calls'] = ajaxCalls.join(",");
				}

				jQuery.ajax({
		            url:controller_opt.ajaxUrl,
		            type: 'post',
		            data: args,
		            success: function(output) {
		                output = JSON.parse(output);
		            	Object.entries(output).forEach(entry => {
						  const [key, value] = entry;
						  jQuery('#'+key).parent().replaceWith(value);
						  jQuery('#'+key).addClass('ajax');
		                  lazyLoad(document.getElementById(key));
						  postCarousel(key);
						  videoTrigger();
						});
		                afterPostFetch();
		            },
		            error:function () {
		                console.log(controller_opt.postError);
		            }
		        });

		    }

		}


		function megamenuAjax(megamenues){
			$.ajax({
                url:controller_opt.ajaxUrl,
                type: 'post',
                data: {
                	action:'megamenu_load',
                	megamenues:megamenues.join('|'),
                },
                success: function(data) {

                	if (!$.isEmptyObject(data)) {

	                	Object.entries(data).forEach(entry => {
							const [key, value] = entry;

							var holder = $('.mm-true[data-megamenu="'+key+'"]');

							if(holder.hasClass('et-button') && !holder.next('#megamenu-'+key).length){
								$(value).insertAfter(holder);
							} else if(!holder.children('#megamenu-'+key).length) {
								holder.append(value);
							}
						});

						etElements();
						megamenuTab();
						megamenuPos();
						videoTrigger();
						megamenuHoverCheck();

						if ($('.et-desktop .et-woo-products').length) {
							ajaxAddToCart();
							listImages();
							quickView();
						}

						var id = $('.et-desktop').attr('id');
						lazyLoad(document.getElementById(id));

						if ($('.sidebar-menu-container.mm').length) {
							lazyLoad(document.getElementById($('.sidebar-menu-container.mm .sidebar-menu').attr('id')));
						}
						
					}

				},
				error: function(data){
					console.log('Something went wrong, please contact site administrator');
				}
            });
		}

		function footerAjax(footer){

			$.ajax({
                url:controller_opt.ajaxUrl,
                type: 'post',
                data: {
                	action:'footer_load',
                	footer:footer,
                },
                success: function(data) {

                	if (!$.isEmptyObject(data)) {

                		if (Object.values(data)[0]) {
                			$('#footer-placeholder-'+Object.keys(data)[0]).replaceWith(Object.values(data)[0]);

							etElements();
							videoTrigger();
							lang_curr_Toggles();

							if ($('.et-footer .et-woo-products').length) {
								ajaxAddToCart();
								listImages();
								quickView();
							}

							var id = $('.et-footer').attr('id');
							lazyLoad(document.getElementById(id));

							stickyFooter();

						}
						
					}

				},
				error: function(data){
					console.log('Something went wrong, please contact site administrator');
				}
            });
		}

		/* loops
		----*/

			var max     	= parseInt(controller_opt.postMax),
				start   	= parseInt(controller_opt.start) + 1,
				request 	= false;

			if ($('.post-layout').hasClass('masonry')) {

				$('.masonry #loop-posts').imagesLoaded(function(){
					var masonry = $('.masonry #loop-posts').masonry({
					  itemSelector: '.post',
					  columnWidth:'.post',
					  percentPosition:true,
					  gutter:0
					});
				});

			}

			if ($('#loop-posts').length) {
				fetchPosts('posts');
			}

			if ($('#loop-products').length) {
				if (!$('#loop-products').parents().hasClass('related') && !$('#loop-products').hasClass('subcategories') && !$('#loop-products').hasClass('both')) {
					
					max  = controller_opt.productMax;

					fetchPosts('products');
				}
			}

		/* product +-
		-----*/

			function toggleDisable(){
            	if($( 'form.cart' ).find( '.qty' ).val() > 1){$('button.minus').removeAttr('disabled');}
            	else if($( 'form.cart' ).find( '.qty' ).val() <= 1){$('button.minus').attr('disabled','disabled');}
            }

            function ProductCount(){
	            $('form.cart').on( 'click', 'button.plus, button.minus', function() {
	 
		            // Get current quantity values
		            var qty  = $( this ).closest( 'form.cart' ).find( '.qty' );
		            var val  = parseFloat(qty.val());
		            var max  = parseFloat(qty.attr( 'max' ));
		            var min  = parseFloat(qty.attr( 'min' ));
		 			var step = parseFloat(qty.attr( 'step' ));
		            // Change the value if plus or minus
		            if ( $( this ).is( '.plus' ) ) {
		               if ( max && ( max <= val ) ) {
		                  qty.val( max );
		               } 
		            else {
		               qty.val( val + step );
		                 }
		            } 
		            else {
		               if ( min && ( min >= val ) ) {
		                  qty.val( min );
		               } 
		               else if ( val > 1 ) {
		                  qty.val( val - step );
		               }
		            }
		            toggleDisable();
		        });

		        $( 'form.cart' ).find( '.qty' ).on('change',function(){
		            toggleDisable();
		        });
	        }

		/* quick-view
		-----*/

			if (typeof(quickview_opt) != "undefined") {
	
				var ProductGallery = function( $target, args ) {
					this.$target = $target;
					this.$images = $( '.woocommerce-product-gallery__image', $target );

					// No images? Abort.
					if ( 0 === this.$images.length ) {
						this.$target.css( 'opacity', 1 );
						return;
					}

					// Make this object available.
					$target.data( 'product_gallery', this );

					// Pick functionality to initialize...
					this.flexslider_enabled = 'function' === typeof $.fn.flexslider && quickview_opt.flexslider_enabled;
					this.zoom_enabled       = 'function' === typeof $.fn.zoom && quickview_opt.zoom_enabled;
					this.photoswipe_enabled = typeof PhotoSwipe !== 'undefined' && quickview_opt.photoswipe_enabled;

					// ...also taking args into account.
					if ( args ) {
						this.flexslider_enabled = false === args.flexslider_enabled ? false : this.flexslider_enabled;
						this.zoom_enabled       = false === args.zoom_enabled ? false : this.zoom_enabled;
						this.photoswipe_enabled = false === args.photoswipe_enabled ? false : this.photoswipe_enabled;
					}

					// ...and what is in the gallery.
					if ( 1 === this.$images.length ) {
						this.flexslider_enabled = false;
					}

					// Bind functions to this.
					this.initFlexslider       = this.initFlexslider.bind( this );
					this.initZoom             = this.initZoom.bind( this );
					this.initZoomForTarget    = this.initZoomForTarget.bind( this );
					this.initPhotoswipe       = this.initPhotoswipe.bind( this );
					this.onResetSlidePosition = this.onResetSlidePosition.bind( this );
					this.getGalleryItems      = this.getGalleryItems.bind( this );
					this.openPhotoswipe       = this.openPhotoswipe.bind( this );

					if ( this.flexslider_enabled ) {
						this.initFlexslider( args.flexslider );
						$target.on( 'woocommerce_gallery_reset_slide_position', this.onResetSlidePosition );
					} else {
						this.$target.css( 'opacity', 1 );
					}

					if ( this.zoom_enabled ) {
						this.initZoom();
						$target.on( 'woocommerce_gallery_init_zoom', this.initZoom );
					}

					if ( this.photoswipe_enabled ) {
						this.initPhotoswipe();
					}
				};

				ProductGallery.prototype.initFlexslider = function( args ) {
					var $target = this.$target,
						gallery = this;

					var options = $.extend( {
						selector: '.woocommerce-product-gallery__wrapper > .woocommerce-product-gallery__image',
						start: function() {
							$target.css( 'opacity', 1 );
						},
						after: function( slider ) {
							gallery.initZoomForTarget( gallery.$images.eq( slider.currentSlide ) );
						}
					}, args );

					$target.flexslider( options );

					// Trigger resize after main image loads to ensure correct gallery size.
					$( '.woocommerce-product-gallery__wrapper .woocommerce-product-gallery__image:eq(0) .wp-post-image' ).one( 'load', function() {
						var $image = $( this );

						if ( $image ) {
							setTimeout( function() {
								var setHeight = $image.closest( '.woocommerce-product-gallery__image' ).height();
								var $viewport = $image.closest( '.flex-viewport' );

								if ( setHeight && $viewport ) {
									$viewport.height( setHeight );
								}
							}, 100 );
						}
					} ).each( function() {
						if ( this.complete ) {
							$( this ).trigger( 'load' );
						}
					} );
				};

			
				ProductGallery.prototype.initZoom = function() {
					this.initZoomForTarget( this.$images.first() );
				};

				ProductGallery.prototype.initZoomForTarget = function( zoomTarget ) {
					if ( ! this.zoom_enabled ) {
						return false;
					}

					var galleryWidth = this.$target.width(),
						zoomEnabled  = false;

					$( zoomTarget ).each( function( index, target ) {
						var image = $( target ).find( 'img' );

						if ( image.data( 'large_image_width' ) > galleryWidth ) {
							zoomEnabled = true;
							return false;
						}
					} );

					// But only zoom if the img is larger than its container.
					if ( zoomEnabled ) {
						var zoom_options = $.extend( {
							touch: false
						}, quickview_opt.zoom_options );

						if ( 'ontouchstart' in document.documentElement ) {
							zoom_options.on = 'click';
						}

						zoomTarget.trigger( 'zoom.destroy' );
						zoomTarget.zoom( zoom_options );

						setTimeout( function() {
							if ( zoomTarget.find(':hover').length ) {
								zoomTarget.trigger( 'mouseover' );
							}
						}, 100 );
					}
				};

				ProductGallery.prototype.initPhotoswipe = function() {
					if ( this.zoom_enabled && this.$images.length > 0 ) {
						this.$target.prepend( '<a href="#" class="woocommerce-product-gallery__trigger">🔍</a>' );
						this.$target.on( 'click', '.woocommerce-product-gallery__trigger', this.openPhotoswipe );
						this.$target.on( 'click', '.woocommerce-product-gallery__image a', function( e ) {
							e.preventDefault();
						});

						// If flexslider is disabled, gallery images also need to trigger photoswipe on click.
						if ( ! this.flexslider_enabled ) {
							this.$target.on( 'click', '.woocommerce-product-gallery__image a', this.openPhotoswipe );
						}
					} else {
						this.$target.on( 'click', '.woocommerce-product-gallery__image a', this.openPhotoswipe );
					}
				};

				ProductGallery.prototype.onResetSlidePosition = function() {
					this.$target.flexslider( 0 );
				};

				ProductGallery.prototype.getGalleryItems = function() {
					var $slides = this.$images,
						items   = [];

					if ( $slides.length > 0 ) {
						$slides.each( function( i, el ) {
							var img = $( el ).find( 'img' );

							if ( img.length ) {
								var large_image_src = img.attr( 'data-large_image' ),
									large_image_w   = img.attr( 'data-large_image_width' ),
									large_image_h   = img.attr( 'data-large_image_height' ),
									alt             = img.attr( 'alt' ),
									item            = {
										alt  : alt,
										src  : large_image_src,
										w    : large_image_w,
										h    : large_image_h,
										title: img.attr( 'data-caption' ) ? img.attr( 'data-caption' ) : img.attr( 'title' )
									};
								items.push( item );
							}
						} );
					}

					return items;
				};

				ProductGallery.prototype.openPhotoswipe = function( e ) {
					e.preventDefault();

					var pswpElement = $( '.pswp' )[0],
						items       = this.getGalleryItems(),
						eventTarget = $( e.target ),
						clicked;

					if ( eventTarget.is( '.woocommerce-product-gallery__trigger' ) || eventTarget.is( '.woocommerce-product-gallery__trigger img' ) ) {
						clicked = this.$target.find( '.flex-active-slide' );
					} else {
						clicked = eventTarget.closest( '.woocommerce-product-gallery__image' );
					}

					var options = $.extend( {
						index: $( clicked ).index(),
						addCaptionHTMLFn: function( item, captionEl ) {
							if ( ! item.title ) {
								captionEl.children[0].textContent = '';
								return false;
							}
							captionEl.children[0].textContent = item.title;
							return true;
						}
					}, quickview_opt.photoswipe_options );

					// Initializes and opens PhotoSwipe.
					var photoswipe = new PhotoSwipe( pswpElement, PhotoSwipeUI_Default, items, options );
					photoswipe.init();
				};

				$.fn.wc_product_gallery = function( args ) {
					new ProductGallery( this, args || quickview_opt );
					return this;
				};

			}

			var quickViewLoading = false;
				
		/* main functions call
		-----*/

			lang_curr_Toggles();
			mobileNavigation();
			mobileContainerTabs();
			containerExtended();
			etElements();
			megamenuTab();
			megamenuPos();
			megamenuHoverCheck();
			stickyFooter();

			listImages();
			ajaxAddToCart();
			quickView();
			ProductCount();
		
			$(window).on('resize',function(){
				megamenuPos();
			});

		/* ajaxes
		----*/

			if (!$('body').hasClass('single-header')) {

				var megamenues = [];

				$('.menu-item.mm-true').each(function(){
					var $this = $(this),
						megamenu = $this.attr('data-megamenu');
					if (typeof(megamenu) != 'undefined') {
						megamenues.push(megamenu);						
					}
				});

				$('.et-button.megamenu-ajax-true').each(function(){
					var $this = $(this),
						megamenu = $this.attr('data-megamenu');
					if (typeof(megamenu) != 'undefined') {
						megamenues.push(megamenu);						
					}
				});

				if (megamenues.length && (window.self === window.top || !window.name.startsWith("customize-preview"))) {
					megamenuAjax(megamenues);
				}

			}

			if (!$('body').hasClass('single-footer')) {

				var footerPlaceholder = $('.footer-placeholder');

				if (footerPlaceholder.length) {
					var footerID = footerPlaceholder.attr('data-footer');
					footerAjax(footerID);
				}

			}

			//loops
			document.addEventListener("DOMContentLoaded", productLoad());
			document.addEventListener("DOMContentLoaded", postLoad());

			let actions = [
		        'filter_attributes',
		        'et__product_filter'
		    ];

			$( document ).ajaxComplete(function( event, xhr, settings ) {

		        if (typeof(settings['data']) != 'undefined' && settings['data'] != null) {

		            var data = decodeURIComponent(settings['data']);

		            data = data.split("&");

		            var dataObj = [{}];

		            for (var i = 0; i < data.length; i++) {
		                var property = data[i].split("=");
		                var key      = (property[0]);
		                var value    = (property[1]);
		                if (typeof(value) != 'undefined') {
		                    dataObj[key] = value;
		                }
		            }

		            if(actions.includes(dataObj['action'])){
		                ajaxAddToCart();
		            }

		        }
		    });

	})(jQuery);

/* Single product
----*/


	function clearResults(inside){
	    inside.removeClass('loading');
	    inside.find('.search-results').empty().addClass('empty');
	    inside.find('.table-wrapper').removeClass('active');
	    inside.find('.vehicle-reset').remove();
	}

	function clearFilter(inside){
	    inside.find('select').val('').trigger('change.select2');
	    inside.find('.vehicle-reset').remove();
	}

	function actionVisibility(inside){
	    if (inside.find('input[type="checkbox"]:checked').length) {
	        inside.find('tfoot').removeClass('hidden');
	    } else {
	        inside.find('tfoot').addClass('hidden');
	    }
	}

	function toggleVehiclesMetabox(universal,inside){
	    if (universal) {

	        jQuery('#enovathemes_addons_products_vehicles_metabox').addClass("hidden");

	        clearResults(inside);
	        clearFilter(inside);

	    } else {
	        jQuery('#enovathemes_addons_products_vehicles_metabox').removeClass("hidden");
	    }
	}

	function vehicleSearch(inside,data){

	    let postData = {};

	    postData['action'] = 'fetch_product_vehicles';
	    postData['attributes'] = JSON.stringify(data);

	    jQuery.ajax({
	        type: 'POST',
	        url: controller_opt.ajaxUrl,
	        data: postData,
	        success: function(output) {

	            if (output) {

	                output = JSON.parse(output);

	                if (!inside.find('.search-results').hasClass('empty')) {

	                    inside.removeClass('loading');
	                    if (!inside.find('a.vehicle-reset').length) {
	                        inside.prepend('<a href="" class="vehicle-reset">'+controller_opt.vehicleReset+'</a><span class="et-clearfix"></span>');
	                    }
	                    if (output['html']) {
	                        inside.find('.table-wrapper').addClass('active');
	                        inside.find('.search-results').html(output['html']);
	                    } else {
	                        inside.find('.search-results').html('<tr><td class="no-results">'+controller_opt.noVehicles+'</td></tr>');
	                    }

	                    actionVisibility(inside);

	                }

	                
	                if (output['next']) {
	                    inside.find('select[name="'+data['next']+'"]').html(output['next']);
	                }

	                // if (output['dev']) {
	                //     console.log(output['dev']);
	                // }

	            } else {
	                clearResults(inside);
	            }

	        },
	        error: function(data) {
	            alert(controller_opt.adminAJAXError);
	        }
	    });
	}

	function fetchFilterData(inside,post_id) {
	        jQuery.ajax({
	        type: 'POST',
	        url: controller_opt.ajaxUrl,
	        data: {
	            'action':'fetch_vehicles_params',
	            'post_id':post_id,
	        },
	        success: function(data) {

	            let output = JSON.parse(data);

	            if (!jQuery('#enovathemes_addons_products_vehicles_metabox .inside input.vehicle-param').length && output['form']) {

	                jQuery('#enovathemes_addons_products_vehicles_metabox .inside .vehicle-admin-filter').remove();
	                jQuery('#enovathemes_addons_products_vehicles_metabox .inside .vehicle-reset').remove();
	                jQuery('#enovathemes_addons_products_vehicles_metabox .inside .et-clearfix').remove();
	                
	                jQuery('#enovathemes_addons_products_vehicles_metabox .inside')
	                .prepend(output['form']);

	                jQuery('#enovathemes_addons_products_vehicles_metabox select').each(function(){
	                    let placeholder = jQuery(this).attr('data-placeholder');

	                    var $this = jQuery(this);

	                    if (jQuery(this).eq(0)) {
	                        jQuery(this).select2({
	                            placeholder:placeholder,
	                            allowClear: true,
	                            dir: controller_opt.lang,
	                            dropdownAutoWidth: true,
                				dropdownParent:$this.parent()
	                        });
	                    } else {
	                        jQuery(this).select2({
	                            multiple: true,
	                            placeholder:placeholder,
	                            allowClear: true,
	                            dir: controller_opt.lang,
	                            dropdownAutoWidth: true,
                				dropdownParent:$this.parent()
	                        });
	                    }
	                });
	            }

	            if (output['html']) {
	                inside.find('.table-wrapper').addClass('active');
	                inside.find('.search-results').html(output['html']);
	            } else {
	                clearResults(inside);
	            }

	            inside.removeClass('loading');

	            actionVisibility(inside);

	        },
	        error: function(data) {
	            alert(controller_opt.adminAJAXError);
	        }
	    });
	}

	function vehicleAssign(inside,data){

	    inside.addClass('loading');

	    data['action'] = 'assign_product_vehicles';

	    jQuery.ajax({
	        type: 'POST',
	        url: controller_opt.ajaxUrl,
	        data: data,
	        success: function(output) {

	            let activeParams = getParams();
	            if (activeParams['product_id']) {
	                fetchFilterData(inside,activeParams['product_id']);
	            }

	        },
	        error: function(data) {
	            alert(controller_opt.adminAJAXError);
	        }
	    });
	}


	if(jQuery('#enovathemes_addons_products_vehicles_metabox').length){

	    let activeParams = getParams();

	    jQuery('#enovathemes_addons_products_vehicles_metabox .inside')
	    .append('<div class="table-wrapper"><table class="search-results" /></div>');

	    let inside = jQuery('#enovathemes_addons_products_vehicles_metabox .inside');

	    // Fetch the filter form
	    fetchFilterData(inside,activeParams['product_id']);

	    // Filter param on change

	    jQuery(document).on('change', "select.vehicle-param", function(e){

	        inside.find('.table-wrapper').removeClass('active');
	        inside.find('.search-results').html('');
	        inside.find('.search-results').removeClass('empty');
	        inside.addClass('loading');

	        let $this = jQuery(this),
	            data = {},
	            next = $this.parents('.select-wrapper').next().find('select').attr('name');

	        data['post_id'] = activeParams['product_id'];

	        if (typeof(next) != 'undefined' && next != null) {
	            data['next'] = next;
	        }

	        if ($this.parent().is(':first-child')) {
	            $this.parents('.vehicle-admin-filter').find('select').not($this).val('').trigger('change.select2');
	        }

	        $this.parent().nextAll().find('select').val('').trigger('change.select2');


	        $this.parents('.vehicle-admin-filter').find('select').each(function(){

	            let thisVal = jQuery(this).val();

	            if (thisVal.length) {
	                data[jQuery(this).attr('name')] = thisVal;
	            }

	        });


	        if(!jQuery.isEmptyObject(data)){
	            vehicleSearch(inside,data);
	        } else {
	           clearResults(inside);
	        }

	    });

	    // Vehicle assign action

	    jQuery(document).on('click', ".vehicle-assign-action", function(e){

	        e.preventDefault();

	        let $this  = jQuery(this),
	            data   = {},
	            assign = [],
	            unsign = [];

	        data['nonce'] = $this.parent().find('input[name="assign-nonce"]').val();
	        data['post_id'] = activeParams['product_id'];

	        inside.find('.search-results tbody input[type="checkbox"]:checked').each(function(){
	            assign.push(jQuery(this).val());
	        });

	        inside.find('.search-results tbody input[type="checkbox"]:not(:checked)').each(function(){
	            unsign.push(jQuery(this).val());
	        });

	        if (assign.length) {
	            data['assign'] = JSON.stringify(assign);
	        }

	        if (unsign.length) {
	            data['unsign'] = JSON.stringify(unsign);
	        }

	        vehicleAssign(inside,data);


	    });

	    // Reset

	    jQuery(document).on('click', ".vehicle-reset", function(e){
	        e.preventDefault();

	        inside.find('.table-wrapper').removeClass('active');
	        inside.find('.search-results').html('');
	        inside.find('.search-results').removeClass('empty');
	        inside.addClass('loading');

	        inside.find('select').val('').trigger('change.select2');

	        clearResults(inside);

	        jQuery(this).remove();
	    });


	    // Checkboxes click

	    jQuery(document).on('click', 'input[name="all"]', function(){
	        inside.find('.search-results tbody input[type="checkbox"]').prop('checked',this.checked);
	    });

	    jQuery(document).on('click', '.search-results input[type="checkbox"]', function(){

	        if (!jQuery(this).is(':checked')) {
	            inside.find('.search-results input[name="all"]').prop('checked',false);
	        }

	        actionVisibility(inside);
	        

	    });
	 
	}