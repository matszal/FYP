var myHeading = document.querySelector('h1');
myHeading.textContent = 'AWS Based ecommerce platform';



function setUserName(){
	var myName = prompt('Please enter your name');
	localStorage.setItem('name', myName);
	myHeading.textContent = myHeading + myName;
	
	if(!localStorage.getItem('name')) {
  setUserName();
} else {
  var storedName = localStorage.getItem('name');
  myHeading.textContent = 'Mozilla is cool, ' + storedName;
}
	
}


var myImage = document.querySelector('img');

myImage.onclick = function() {
    var mySrc = myImage.getAttribute('src');
    if(mySrc === 'images/icon-cloud-aws.png') {
      myImage.setAttribute ('src','images/js.png');
    } else {
      myImage.setAttribute ('src','images/firefox-icon.png');
    }
}


var myButton = document.querySelector('button');
var myHeading = document.querySelector('h1');