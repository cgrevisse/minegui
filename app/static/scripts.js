var MAX_STARS = 5


//SentenceHighlight "object" created from entities or interactions
function SentenceHighlight(start,end,type,color) {
    this.start = start;
    this.end=end;
    this.color = color;
	this.type=type;
}

//compare function for SentenceHighlight objects: criteria=start attribute
function compareStart(a,b) {
  if (a.start > b.start)
     return -1;
  if (a.start < b.start)
    return 1;
  return 0;
}


function populateSentenceList() {
    
    // start loader animation
    var progress;
    $('body').loadie();
    
    progress = .1
    $('body').loadie(progress);
    
    $.ajax({
        url: '/sentences',
        type: 'GET',
        data: {},
        dataType: 'json',
        success: function(data) {
            var list = $("#sentenceList");
            
            progress = .5
            $('body').loadie(progress);
            
            var numberOfElements = data.length;
            var i = 0;
            $.each(data, function() {
                var tr = $('<tr>');
                
				var sentenceHighlightArray = [];
				$.each(this.entities, function() {
					sentenceHighlightArray.push(new SentenceHighlight(parseInt(this.start),parseInt(this.end),this.type,"label label-success"));
				});
				
				$.each(this.interactions, function() {
					sentenceHighlightArray.push(new SentenceHighlight(parseInt(this.start),parseInt(this.end),this.type,"label label-danger"));
				});
				//order entities and interactions by the start position
				sentenceHighlightArray.sort(compareStart);
				var index=0;
				var highlightedSentence="";
				var initialSentence=this.literal;
				var popFromArray=true;
				//generate highlighted sentence
				while(sentenceHighlightArray.length>0){
					var sh;
					if(popFromArray){
						sh=sentenceHighlightArray.pop();
					}
					if(index<sh.start){//non highlighted text
						highlightedSentence=highlightedSentence+initialSentence.slice(index,sh.start);
						index=sh.start;
						popFromArray=false;
					}else if(index==sh.start){
						highlightedSentence=highlightedSentence+'<span title="'+sh.type +'"><span class="'+sh.color+'">'+initialSentence.slice(sh.start,sh.end)+'</span></span>';
						index=sh.end;
						popFromArray=true;
					}else{//if index < start skip the entity, as this part of the sentence was already highlighted
						popFromArray=true;
					}
				}
				//add rest of non-highlighted text
				highlightedSentence=highlightedSentence+initialSentence.slice(index);
				tr.append($('<td class="sentenceLine" title="' + this.id +'"><div class="truncate">' + highlightedSentence + '</div></td>'));
                
                tr.append($('<td>' + this.score + '</td>'));
                

				var stars='<div id="SentenceGrade_'+this.id+'" class="rateit" data-rateit-value="'+this.grade+'" data-rateit-ispreset="true" data-rateit-readonly="true"></div>';
				tr.append($('<td>' + stars +'</td>'))
                
				//open gradeing popup button
                tr.append($('<td><button type="button" class="btn btn-warning btn-xs" data-sentenceid="'+ this.id +'"><span class="glyphicon glyphicon-tasks"></span> Curate</button></td>'));
                
                list.append(tr);
				//display grading stars
                $('#SentenceGrade_'+this.id).rateit();
                i++;
                progress += (i/numberOfElements)/2;
                $('body').loadie(progress);
            });

            $('.sentenceLine').mouseenter(function() {}).mouseleave(function() {}).click(function() {
                
                // truncate all
                $.each($(".sentenceLine"), function() {
                    $(this).children().first().addClass('truncate');
                });
                
                // show detail of clicked sentence
                $(this).children().first().removeClass('truncate');
                
                // load metadata of related paper
                var id = $(this).attr('title');
                
                $("#metaData").hide("fast");
                
                $.ajax({
                    url: '/sentences/' + id + '/metadata',
                    type: 'GET',
                    data: {},
                    dataType: 'json',
                    success: function(data) {
                        $("#metaDataPubMedID").attr("href", "http://www.ncbi.nlm.nih.gov/pubmed/?term=" + data.pmid).text(data.pmid);
                        $("#metaDataDOI").attr("href", "http://dx.doi.org/" + data.doi).text(data.doi);
                        $("#metaDataTitle").text(data.title);
                        $("#metaDataAuthors").text(data.authors.join("; "));
                        $("#metaDataJournal").text(data.journal);
                        $("#metaDataYear").text(data.year);
                        $("#metaDataAbstract").text(data.abstract);
                        $("#metaData").slideDown();
                    }
                });
            });
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log("Error " + xhr.status + ": " + thrownError);
        }
    });
}

function addGradeDialogButtonOnClickListener(){
$(document).on('click', '.btn.btn-warning.btn-xs', function () {
		var sentenceId = jQuery(this).data('sentenceid');
     
       
	   $.ajax({
        url: '/sentences/'+sentenceId,
        type: 'GET',
        data: {},
        dataType: 'json',
        success: function(data) {
	
			var html='<div class="modal fade" id="curateModal" tabindex="-1" role="dialog">';
			html+='	    <div id="gradedialogwidth" class="modal-dialog">';
			html+='		<div class="modal-content">';
			html+='		    <div class="modal-header">';
			html+='			<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>';
			html+='			<h4 class="modal-title">Feedback form</h4>';
			html+='		    </div>';
					    
			html+='		    <form id="gradingForm" enctype="multipart/form-data" action="';
			html+="/feedback/";
			html+='" method="post">';
			html+='		    	<div class="modal-body">';
			html+='				<table class="table table-striped">';
			html+='				<thead>';
			html+='					<tr>';
			html+='						<th>Entity</th>';
			html+='						<th>Pattern</th>';
			html+='						<th>Grade</th>';
			html+='						<th>Comment</th>';
			html+='					</tr>';
			html+='				</thead>';
			html+='				<tbody>';
			html+='<input type="hidden" name="SentenceID" value="'+data.id+'"/>';
			html+='					<tr>';
			html+='						<td>Overall feedback</td>';
			html+='						<td></td>';
			html+='						<td><input name="SentenceGrade" type="range" value="'+data.grade+'" id="range'+data.id+'"><div class="rateit" data-rateit-backingfld="#range'+data.id+'"  data-rateit-resetable="false" data-rateit-ispreset="true" data-rateit-min="0" data-rateit-max="5" data-rateit-step="1"></div></td>';
			html+='						<td><textarea name="SentenceComment" class="form-control" rows="1" id="SentenceComment">'+data.comment+'</textarea></td>';
			html+='					</tr>';
			
			var i=0;
			$.each(data.entities, function() {
				html+='<input type="hidden" name="EntityID_'+i+'" value="'+this.id+'"/>';
				html+='					<tr>';
				html+='						<td><span title="'+this.type+'" data-protein="'+data.literal.slice(this.start,this.end)+'"><span class="label label-success">'+data.literal.slice(this.start,this.end)+'</span></span></td>';
				html+='						<td>'+this.name+'</td>';
				html+='						<td><input name="EntityGrade_'+i+'" type="range" value="'+this.grade+'" id="Entityrange'+this.id+'"><div class="rateit" data-rateit-backingfld="#Entityrange'+this.id+'"  data-rateit-resetable="false" data-rateit-ispreset="true" data-rateit-min="0" data-rateit-max="5" data-rateit-step="1"></div></td>';
				html+='						<td><textarea name="EntityComment_'+i+'" class="form-control" rows="1" id="EntityComment_'+i+'">'+this.comment+'</textarea></td>';
				html+='					</tr>';
				i=i+1;
			});
			i=0;
			html+='<input type="hidden" name="entity_num" value="'+data.entities.length+'"/>';
			$.each(data.interactions, function() {
				html+='<input type="hidden" name="InteractionID_'+i+'" value="'+this.id+'"/>';
				html+='					<tr>';
				html+='						<td><span title="'+this.type+'" data-protein="'+data.literal.slice(this.start,this.end)+'"><span class="label label-danger">'+data.literal.slice(this.start,this.end)+'</span></span></td>';
				html+='						<td>'+this.type+'</td>';
				html+='						<td><input name="InteractionGrade_'+i+'" type="range" value="'+this.grade+'" id="Interactionrange'+this.id+'"><div class="rateit" data-rateit-backingfld="#Interactionrange'+this.id+'"  data-rateit-resetable="false" data-rateit-ispreset="true" data-rateit-min="0" data-rateit-max="5" data-rateit-step="1"></div></td>';
				html+='						<td><textarea name="InteractionComment_'+i+'" class="form-control" rows="1" id="InteractionComment_'+i+'">'+this.comment+'</textarea></td>';
				html+='					</tr>';
				i=i+1;
			});
			html+='<input type="hidden" name="interaction_num" value="'+data.interactions.length+'"/>';
			html+='					</tbody>';
			html+='				</table>			';
			html+='			</div>';
			html+='			<div class="modal-footer">';
			html+='				<button type="button" class="btn btn-danger" data-dismiss="modal">Cancel</button>';
			html+='			    <button type="button" onclick="sendDataWithAjax()" class="btn btn-success">Save</button>';
			html+='			</div>';
			html+='		    </form>';
			html+='		</div>';
			html+='	    </div>';
			html+='</div>';
			$('#gradeContainer').html(html);
			$('.rateit').rateit();
			$('#gradedialogwidth').css({
				'width': function () { 
				return ($(document).width() * .5) + 'px';  
			}
			});
			$('#curateModal').modal('show');
			
		},
		error: function (xhr, ajaxOptions, thrownError) {
            console.log("Error " + xhr.status + ": " + thrownError);
        }
		});
		
		
        return false;
    });
}

function sendDataWithAjax(){
$.ajax({
	url: "/feedback/",
	type: "post",
	data: $('#gradingForm').serialize(),
	dataType: 'json',
    success: function(data) {
		$('#curateModal').modal('hide');
		$('#SentenceGrade_'+data.id).data('rateit-value',data.grade);
		$('#SentenceGrade_'+data.id).rateit();
	}
	});

}

$(function() {
    populateSentenceList();
	addGradeDialogButtonOnClickListener();
});