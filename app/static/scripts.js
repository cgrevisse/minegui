var MAX_STARS = 5

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
                
                // TODO: mark keywords with colors and show type in title
                // e.g. <span title="PROTEIN"><span class="label label-success">Hsp90</span></span> regulates <span title="PROTEIN"><span class="label label-success">PINK1</span></span> <span title="PATTERN Protein_catabolism"><span class="label label-danger">stability </span></span>. 
                tr.append($('<td class="sentenceLine" title="' + this.id +'"><div class="truncate">' + this.literal + '</div></td>'));
                
                tr.append($('<td>' + this.score + '</td>'));
                
                //var stars = "";
                //for(var i = 1; i <= this.grade; i++) stars += '<span class="glyphicon glyphicon-star"></span>'
                //for(var i = this.grade + 1; i <= MAX_STARS; i++) stars += '<span class="glyphicon glyphicon-star-empty"></span>'
                var stars='<div class="rateit" data-rateit-value="'+this.grade+'" data-rateit-ispreset="true" data-rateit-readonly="true"></div>';
				tr.append($('<td>' + stars +'</td>'))
                
                // TODO: use this.id to open popup and load data from REST interface /sentences/<id>
                tr.append($('<td><button type="button" class="btn btn-warning btn-xs" data-sentenceid="'+ this.id +'"><span class="glyphicon glyphicon-tasks"></span> Curate</button></td>'));
                
                list.append(tr);
                
                i++;
                progress += (i/numberOfElements)/2;
                $('body').loadie(progress);
            });
			//display grading stars
            $('.rateit').rateit();
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
					    
			html+='		    <form enctype="multipart/form-data" action="';
			html+="{{ url_for('index') }}";
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
			$.each(data.entities, function() {
				html+='					<tr>';
				html+='						<td><span title="'+this.type+'" data-protein="'+data.literal.slice(this.start,this.end)+'"><span class="label label-success">'+data.literal.slice(this.start,this.end)+'</span></span></td>';
				html+='						<td>'+this.name+'</td>';
				html+='						<td><div class="rateit" data-rateit-value="'+this.grade+'" data-rateit-ispreset="true" data-rateit-step="1"></div></td>';
				html+='						<td><textarea class="form-control" rows="5" id="comment">'+this.comment+'</textarea></td>';
				html+='					</tr>';
			});
			$.each(data.interactions, function() {
				html+='					<tr>';
				html+='						<td><span title="'+this.type+'" data-protein="'+data.literal.slice(this.start,this.end)+'"><span class="label label-danger">'+data.literal.slice(this.start,this.end)+'</span></span></td>';
				html+='						<td>'+this.type+'</td>';
				html+='						<td><div class="rateit" data-rateit-value="'+this.grade+'" data-rateit-ispreset="true" data-rateit-step="1"></div></td>';
				html+='						<td><textarea class="form-control" rows="5" id="comment">'+this.comment+'</textarea></td>';
				html+='					</tr>';
			});
			html+='					<tr>';
			html+='						<td>Overall feedback</td>';
			html+='						<td></td>';
			html+='						<td><div class="rateit" data-rateit-value="'+data.grade+'" data-rateit-ispreset="true" data-rateit-step="1"></div></td>';
			html+='						<td><textarea class="form-control" rows="5" id="comment">'+data.comment+'</textarea></td>';
			html+='					</tr>';
			html+='					</tbody>';
			html+='				</table>			';
			html+='			</div>';
			html+='			<div class="modal-footer">';
			html+='				<button type="submit" class="btn btn-danger">Cancel</button>';
			html+='			    <button type="submit" class="btn btn-success">Save</button>';
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


$(function() {
    populateSentenceList();
	addGradeDialogButtonOnClickListener();
});