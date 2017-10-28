var myHeading = document.querySelector('h1');
myHeading.textContent = 'AWS Based ecommerce platform';

var myImage = document.querySelector('img');

myImage.onclick = function() {
    var mySrc = myImage.getAttribute('src');
    if(mySrc === 'images/icon-cloud-aws.png') {
      myImage.setAttribute ('src','images/js.png');
    } else {
      myImage.setAttribute ('src','images/firefox-icon.png');
    }
}