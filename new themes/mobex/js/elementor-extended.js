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

jQuery( window ).on( 'elementor/frontend/init', () => {


    elementorFrontend.hooks.addAction( 'frontend/element_ready/container', function( $scope ) {


    	/* Responsive
    	-----------------------*/

	    	let breakpoints = ['breakpoint-767','breakpoint-768-1023','breakpoint-1024-1279','breakpoint-1280-1365','breakpoint-1366'];

	    	for (var i = 0; i < breakpoints.length; i++) {
	    		if($scope.children('.element-shadow').length && $scope.children('.element-shadow').hasClass(breakpoints[i])){
					$scope.addClass(breakpoints[i]);
				}

				else {
					$scope.removeClass(breakpoints[i]);
				}
	    	}

	    /* Goldshine
    	-----------------------*/
		
	        if($scope.children('.element-shadow.gold-shine').length){
	            $scope.addClass('gold-shine');
	        }

	        else {
	        	$scope.removeClass('gold-shine');
	        }

	    /* Gradient
    	-----------------------*/
		
	        if($scope.children('.element-shadow.gradient').length){
	            $scope.addClass('gradient');
	        }

	        else {
	        	$scope.removeClass('gradient');
	        }

	    /* Parallax
    	-----------------------*/
		
	        if($scope.children('.element-shadow.et-parallax').length){

	            $scope.addClass('et-parallax');

	        	var parallax = $scope.children('.element-shadow.et-parallax'),
	        		duration = parseInt(parallax.data('parallax-duration')),
	        		image    = parallax.data('parallax-image'),
	            	ratio    = (typeof(duration) != 'undefined' && duration != null && duration != 0) ? 0.5 : 1;

	            if (duration == null) {duration = 0;}

	            duration = duration/100;

	        	jQuery('<div class="parallax-container active" style="background-image:url('+image+');" />').insertBefore(parallax);
	            	
	            var plx = $scope.find('.parallax-container');

	            jQuery(window).scroll(function() {
	                var yPos = Math.round((jQuery(window).scrollTop()-plx.offset().top) / 1.5);

	                yPos = ratio*yPos;

	                gsap.to(plx,{
	                	duration:duration,
	                	delay:0,
	                	y:yPos,
	            	});
	            });
	        	
	        } else {
	        	$scope.removeClass('et-parallax').children('.parallax-container').remove();
	        }

	    /* Mobile tab item
		-----------------------*/

	        if($scope.children('.element-shadow.mobile-tab-item').length){
	        	$scope.addClass('mobile-tab-item');
	        }

	        else {
	        	$scope.removeClass('mobile-tab-item');
	        }

	    /* Container as stagger box
		-----------------------*/

	        if ($scope.children('.element-shadow.et-stagger-box').length) {

	        	$scope.addClass('et-stagger-box').removeClass('stagger-active');

	        	var shadow    = $scope.children('.element-shadow.et-stagger-box'),
					delay     = '+='+(0.2 + parseInt(shadow.data('delay'))/1000),
					interval  = parseInt(shadow.data('interval'))/1000,
					stagger   = shadow.data('stagger'),
					content   = $scope.children('.e-con-inner').length ? 
					$scope.children('.e-con-inner').children('.elementor-element').not('.elementor-widget-et_gap') : 
					$scope.children('.elementor-element').not('.elementor-widget-et_gap');

				content.addClass('stagger-item').removeAttr('style');

				var tl = new gsap.timeline({paused: true});

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

				$scope.addClass('stagger-active');

	        	tl.progress(0);
				tl.play();

	        }

	        else if($scope.hasClass('et-stagger-box')) {
	        	$scope
	        	.removeClass('et-stagger-box')
	        	.removeClass('stagger-active')
	        	.find('.stagger-item')
	        	.removeAttr('style')
	        	.removeClass('stagger-item');
	        }

	    /* Popup banner
    	-----------------------*/

	        if($scope.children('.element-shadow.et-popup-banner').length){

				var popup  = $scope.children('.element-shadow.et-popup-banner');
				var	$delay = popup.attr('data-popup-delay');
				var	effect = popup.attr('data-popup-effect');

				$scope.addClass('et-popup-banner').attr('data-popup-effect',effect);

				if (!$scope.parent('.et-popup-banner-wrapper').length) {

					$scope.wrap('<div class="et-popup-banner-wrapper"></div>')
					$scope.prepend('<div class="popup-banner-toggle"></div>');

				} else {
					$scope.parent().removeClass('animate');
				}

				setTimeout(function(){
					$scope.parent().addClass('animate');
				},$delay);

				$scope.find('.popup-banner-toggle').bind('click',function(){
					$scope.parent().removeClass('animate');
				});

	        }

	        else {
	        	$scope.removeClass('et-popup-banner').unwrap('.et-popup-banner-wrapper');
	        	$scope.find('.popup-banner-toggle').remove();
	        }

	    /* Toggle banner
    	-----------------------*/

	        if($scope.children('.element-shadow.et-toggle-banner').length) {

				var toggle = $scope.children('.element-shadow.et-toggle-banner');
				var cookie = toggle.attr('data-cookie');

				if (!$scope.parent('.et-toggle-banner-wrapper').length) {

					$scope.wrap('<div class="et-toggle-banner-wrapper"></div>')
					$scope.prepend('<div class="toggle-banner-toggle"></div>');

				} else {
					$scope.parent().removeClass('animate');
				}

				$scope.parent().addClass('animate');
				
				$scope.find('.toggle-banner-toggle').bind('click',function(){
					jQuery(this).addClass('hide');
					$scope.parent().slideUp(300);
				});
							
	        }

	        else {
	        	$scope.unwrap('.et-toggle-banner-wrapper');
	        	$scope.find('.toggle-banner-toggle').remove();
	        }

	    /* Container as tabs
		-----------------------*/

	        if($scope.children('.element-shadow.section-tab').length){

	        	var sectionTab = $scope.children('.element-shadow.section-tab');
				var $children  = $scope.children('.e-con-inner').length ? $scope.children('.e-con-inner').children('.e-con') : $scope.children('.e-con');

	        	if (typeof($children) != "undefined") {

	        		var tabset = '<div class="tabset section-tabset section-tabs-component">';

	        		$children.wrapAll('<div class="section-tabs-container tabs-container section-tabs-component" />');

					$children.each(function(){

						var tab    = jQuery(this).addClass('section-tab-item').addClass('tab-content'),
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

					jQuery(tabset).insertBefore($scope.find('.section-tabs-container'));

					$scope.find('.section-tabs-component').wrapAll('<div class="section-tab '+sectionTab.data('section-tabs-type')+'" />');

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

						var $thiz = jQuery(this);

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

								tabsContent.hide(0).removeClass('active');
								tabsContent.eq($self.index()).show(0).addClass('active');
								
							}
						});
						
					}

				}

	        }

	        else if($scope.children('.section-tabset').length) {

	        	$scope.find('.section-tabs-container .section-tab-item')
	        	.removeClass('section-tab-item')
	        	.removeClass('tab-content')
	        	.unwrap('.section-tabs-container')
	        	.unwrap('.section-tab');

	        	$scope.find('.section-tabset').eq(0).remove();
	        }

			if ($scope.children('.element-shadow.section-tab-item').length) {

	        	setTimeout(function(){

	        		$scope.parent('.section-tabs-container').prev('.section-tabset').children('.section-tab-item').eq($scope.index()).children('.txt').html($scope.children('.element-shadow.section-tab-item').attr('data-section-tab-title'));
	        	
	        		if (typeof($scope.children('.element-shadow.section-tab-item').attr('data-section-tab-icon')) != "undefined" && $scope.children('.element-shadow.section-tab-item').attr('data-section-tab-icon').length) {
						if ($scope.parent('.section-tabs-container').prev('.section-tabset').children('.section-tab-item').eq($scope.index()).children('.tab-icon').length) {
							$scope.parent('.section-tabs-container').prev('.section-tabset').children('.section-tab-item').eq($scope.index()).children('.tab-icon').attr('style','mask: url('+$scope.children('.element-shadow.section-tab-item').attr('data-section-tab-icon')+') no-repeat 50% 50%;-webkit-mask: url('+$scope.children('.element-shadow.section-tab-item').attr('data-section-tab-icon')+') no-repeat 50% 50%;margin-right: 8px;width: 20px;height: 20px;');
						} else {
							$scope.parent('.section-tabs-container').prev('.section-tabset').children('.section-tab-item').eq($scope.index()).prepend('<span class="tab-icon section-tab-icon" style="mask: url('+$scope.children('.element-shadow.section-tab-item').attr('data-section-tab-icon')+') no-repeat 50% 50%;-webkit-mask: url('+$scope.children('.element-shadow.section-tab-item').attr('data-section-tab-icon')+') no-repeat 50% 50%;margin-right: 8px;width: 20px;height: 20px;"></span>');
						}
					}

	        	},1);

	        }

	    /* Container as accordion
		-----------------------*/

	        if($scope.children('.element-shadow.section-accordion').length) {

	        	var sectionAccordion = $scope.children('.element-shadow.section-accordion');
				var $children       = $scope.children('.e-con-inner').length ? $scope.children('.e-con-inner').children('.e-con') : $scope.children('.e-con');

		    	if (typeof($children) != "undefined") {

		    		$scope.attr("data-accordion-enabled",'true');

		    		var sectionAccordionHTML = sectionAccordion[0].hasAttribute('data-section-accordion-type') ? 
		    		'<div class="section-accordion collapsible-'+sectionAccordion.data('section-accordion-type')+'"/>' :
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

					var $self = jQuery(this);

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

	        }

	        else if($scope.is('[data-accordion-enabled]')) {
	        	$scope
	        	.removeClass('section-accordion-content')
	        	.removeClass('section-accordion-item')
	        	.find('.elementor-element')
	        	.prev('.accordion-title')
	        	.remove();

	        	$scope
	        	.find('.elementor-element')
	        	.unwrap('.section-accordion');
	        }

			if ($scope.children('.element-shadow.section-accordion-item').length) {
	        	
	        	setTimeout(function(){
	        		$scope.prev('.section-accordion-title').children('.txt').html($scope.children('.element-shadow.section-accordion-item').attr('data-section-accordion-title'));

	        		if (typeof($scope.children('.element-shadow.section-accordion-item').attr('data-section-accordion-icon')) != "undefined" && $scope.children('.element-shadow.section-accordion-item').attr('data-section-accordion-icon').length) {
						if ($scope.prev('.section-accordion-title').children('.accordion-icon').length) {
							$scope.prev('.section-accordion-title').children('.accordion-icon').attr('style','mask: url('+$scope.children('.element-shadow.section-accordion-item').attr('data-section-accordion-icon')+') no-repeat 50% 50%;-webkit-mask: url('+$scope.children('.element-shadow.section-accordion-item').attr('data-section-accordion-icon')+') no-repeat 50% 50%;margin-right: 8px;width: 20px;height: 20px;');
						} else {
							$scope.prev('.section-accordion-title').prepend('<span class="accordion-icon section-accordion-icon" style="mask: url('+$scope.children('.element-shadow.section-accordion-item').attr('data-section-accordion-icon')+') no-repeat 50% 50%;-webkit-mask: url('+$scope.children('.element-shadow.section-accordion-item').attr('data-section-accordion-icon')+') no-repeat 50% 50%;margin-right: 8px;width: 20px;height: 20px;"></span>');
						}
					}
	        	},1);

	        }

	    /* Container as carousel
		-----------------------*/

	        if($scope.children('.element-shadow.section-carousel').length){

	        	var carousel  = $scope.children('.element-shadow.section-carousel');
				var $children = $scope.children('.e-con-inner').length ? $scope.children('.e-con-inner').children('.e-con') : $scope.children('.e-con');

				if (!$scope.find('.container-swiper').length) {

					$scope.attr("data-carousel-enabled",'true');
					$children.addClass('section-carousel-child');

					var id        = $scope.data('id'),
						items     = $children.length,
						desktop   = carousel.data('carousel-columns'),
						mobile    = carousel.data('carousel-mobile-columns'),
		 				tabletP   = carousel.data('carousel-tablet-portrait-columns'),
						tabletL   = carousel.data('carousel-tablet-landscape-columns'),
						gatter    = carousel.data('carousel-gatter'),
						autoplay  = carousel.data('carousel-autoplay'),
						navType   = carousel.data('carousel-navigation-type'),
						navPos    = carousel.data('carousel-navigation-position');

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

					$scope.find('.swiper-container')
					.append('<div id="prev-'+id+'" class="container-swiper-nav swiper-button swiper-button-prev"></div><div id="next-'+id+'" class="container-swiper-nav swiper-button swiper-button-next"></div><div id="swiper-pagination-'+id+'" class="swiper-pagination container-swiper-nav"></div>');

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
								slidesPerView: tabletP + ((items == tabletP) ? 0 : 0.4)
							},
							1024: {
								slidesPerView: tabletL + ((items == tabletL) ? 0 : 0.4)
							},
							1280: {
								slidesPerView: desktop,
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
							lazyLoad($scope[0]);
						});
					}

				}

	        }

	        else if($scope.is('[data-carousel-enabled]')) {

	        	console.log($scope.attr('data-carousel-enabled'));

	        	$scope.removeAttr('data-carousel-enabled')
	        	.find('.section-carousel-child')
	        	.removeClass('swiper-slide')
	        	.removeClass('section-carousel-child')
	        	.unwrap('.swiper-wrapper')
	        	.unwrap('.swiper')
	        	.unwrap('.swiper-container');
	        }


    });


});