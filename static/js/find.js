
//function handleIt() {

function search(e) {
    let inputValue=document.getElementById("search").value.trim();    
    if (inputValue !== "") {
        let text = document.getElementByName("main").innerHTML;
        let re = new RegExp(inputValue,"g"); // search for all instances
          let newText = text.replace(re, `<mark>${inputValue}</mark>`);
          document.getElementByName("main").innerHTML = newText;
    }
  }
   /*  {

        var inputValue=document.getElementById("search").value;    
        //$( "main:contains(inputValue)" ).css( "backgound-color", "blue" );




        /* if (window.find(inputValue, true)) { 
    //    document.execCommand("hiliteColor", false, "FirstColor");
        while (window.find(inputValue, true)) {
           document.execCommand("hiliteColor", false, "SecondColor");
        } */
            
  /* setTimeout(function() {
        find(inputValue);
   });
    
}
 */



