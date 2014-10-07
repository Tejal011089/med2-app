

wn.pages['attendance-upload'].onload = function(wrapper) {
wrapper.app_page = wn.ui.make_app_page({
               parent: wrapper,
               title: "Attendance Upload Tool"
       });
$(wrapper).find('.layout-main-section').append('<h3></h3>\
               <p class="help"></p>\
               <div id="dit-upload-area"></div><br>\
               <div class="dit-progress-area" style="display: None"></div>\
               <p id="dit-output"></p>\
               ');
       $select = $(wrapper).find('[name="dit-doctype"]');
       wn.messages.waiting($(wrapper).find(".dit-progress-area").toggle(false),
               "Please wait... upload in progress", 100);
       // upload
       wn.upload.make({
               parent: $('#dit-upload-area'),
               args: {
                       method: 'hr.page.attendance_upload.attendance_upload.upload'
               },
               callback: function(r) {
                       console.log(r.message);
                       //alert(r.message);
                      $(wrapper).find(".dit-progress-area").toggle(false);
                       if(r.message){
			alert("uploaded attendance");
			}             
                      
               }
       });

 // add overwrite option
 var $submit_btn = $('#dit-upload-area input[type="submit"]');
 $('<input type="checkbox" name="overwrite" style="margin-top: -3px">\
   <span> Update</span>\
   <p class="help"></p><br>')
   .insertBefore($submit_btn);
       // rename button
       $('#dit-upload-area form input[type="submit"]')
               .attr('value', 'Upload and Import')
               .click(function() {
                       $('#dit-output').empty();
                       $(wrapper).find(".dit-progress-area").toggle(true);
               });
}
