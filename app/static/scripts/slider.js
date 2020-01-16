function nextSlide() {
    document.querySelectorAll('#slides .slide')[currentSlide].className = "slide";
    currentSlide = (currentSlide+1)%document.querySelectorAll('#slides .slide').length;
    document.querySelectorAll('#slides .slide')[currentSlide].className = "show slide";
}

var currentSlide = 0;
var slideInterval = setInterval(nextSlide,4000);