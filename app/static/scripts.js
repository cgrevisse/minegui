//SentenceHighlight "object" created from entities or interactions
function SentenceHighlight(start,end,type,color, databaseID) {
    this.start = start;
    this.end = end;
    this.color = color;
    this.type = type;
    this.databaseID = databaseID;
}

//compare function for SentenceHighlight objects: criteria=start attribute
function compareStart(a,b) {
    if (a.start > b.start)
         return -1;
    if (a.start < b.start)
        return 1;
    return 0;
}

function updateOntologyLinks() {
    $('.label-protein').each(function() {
        var databaseID = $(this).attr('data-databaseID');
        // TODO: Link proteins to HGNC ontology
        // $(this).contents().wrap('<a href="http://www.genenames.org/' + databaseID + '" target="_blank"></a>');
    });
    
    $('.label-disease').each(function() {
        var databaseID = $(this).attr('data-databaseID').replace("DOID:", "");
        $(this).contents().wrap('<a href="http://disease-ontology.org/term/DOID%3A' + databaseID + '" target="_blank"></a>');
    });
    
    $('.label-go-process').each(function() {
        var databaseID = $(this).attr('data-databaseID');
        $(this).contents().wrap('<a href="http://www.ebi.ac.uk/QuickGO/GTerm?id=' + databaseID + '" target="_blank"></a>');
    });
    
    $('.label-chemical').each(function() {
        var databaseID = parseInt($(this).attr('data-databaseID').replace("CID", ""));
        $(this).contents().wrap('<a href="https://pubchem.ncbi.nlm.nih.gov/compound/' + databaseID + '" target="_blank"></a>');
    });
}

function createHighlightedSentence(row) {
    
    var sentenceHighlightArray = [];
    $.each(row.entities, function() {
        sentenceHighlightArray.push(new SentenceHighlight(parseInt(this.start), parseInt(this.end), this.type, "label label-" + this.type.toLowerCase(), this.databaseID));
    });
    $.each(row.interactions, function() {
        sentenceHighlightArray.push(new SentenceHighlight(parseInt(this.start), parseInt(this.end), this.type, "label label-pattern", ""));
    });
    
    // order entities and interactions by the start position
    sentenceHighlightArray.sort(compareStart);
    var index = 0;
    var highlightedSentence = "";
    var initialSentence = row.literal;
    var popFromArray = true;
    
    // generate highlighted sentence
    while(sentenceHighlightArray.length > 0) {
        var sh;
        if(popFromArray) {
            sh = sentenceHighlightArray.pop();
        }
        
        if(index < sh.start) {
            // non highlighted text
            highlightedSentence = highlightedSentence + initialSentence.slice(index,sh.start);
            index = sh.start;
            popFromArray = false;
        } else if(index == sh.start) {
            highlightedSentence = highlightedSentence + '<span title="' + sh.type + '"><span class="' + sh.color + '" data-databaseID="' + sh.databaseID + '">' + initialSentence.slice(sh.start, sh.end) + '</span></span>';
            index = sh.end;
            popFromArray = true;
        } else {
            //if index < start skip the entity, as this part of the sentence was already highlighted
            popFromArray=true;
        }
    }
    
    //add rest of non-highlighted text
    highlightedSentence = highlightedSentence + initialSentence.slice(index);
            
    return highlightedSentence;
}

function loadMetaData(id) {
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
}

function searchField() {
    return $(".dataTables_filter input");
}

function populateSentenceList() {
    
    $('#sentenceTable').dataTable({
        "ajax": "/sentences",
        "columnDefs": [
            {
                "targets": 0,
                "data": null,
                "render": function(data, type, row) {
                    return '<div class="sentenceLine truncate" data-id="' + row["id"] + '">' + createHighlightedSentence(row) + '</div>';
                }
            },
            {
                "targets":1,
                "data":"score",
                "searchable": false
            },
            {
                "targets": 2,
                "data": "grade",
                "render": function(data, type, row) {
                    return '<div id="SentenceGrade_'+row["id"]+'" class="rateit" data-rateit-value="'+data+'" data-rateit-ispreset="true" data-rateit-readonly="true"></div>'
                },
                "iDataSort": 3,
                "searchable": false
            },
            {
                // additional for sorting
                "targets":3,
                "data": "grade",
                "visible":false,
                "searchable": false
            },
            {
                // open gradeing popup button
                "targets":4,
                "data": null,
                "render": function(data, type, row) {
                    return '<button type="button" class="btn btn-warning btn-xs" data-sentenceid="'+ row["id"] +'"><span class="glyphicon glyphicon-tasks"></span> Curate</button>'
                },
                "bSortable": false,
                "searchable": false
            },
            {
                "targets":5,
                "data":null,
                "render": function(data, type, row) {
                    return JSON.stringify(row);
                },
                "visible":false    
            }
        ],
        "order": [[ 3, "desc" ]],
        "paging":false,
        "fnDrawCallback": function(oSettings) { // fnInitComplete
            // display grading stars
            $(".rateit").rateit();
            
            // update ontology links
            updateOntologyLinks();
            
            // make search field a little prettier
            searchField().addClass("form-control").attr("placeholder", "Filter ...");
            
            // delay search until 3 characters entered
            /*
            var dtable = $("#sentenceTable").dataTable().api();
            searchField()
                .unbind() // Unbind previous default bindings
                .bind("keyup", function(event) { // Bind our desired behavior
                    // If (the length is 3 or more characters, or) the user pressed ENTER, search
                    if(event.keyCode == 13) {
                        // Call the API search function
                        dtable.search(this.value).draw();
                    }
                    // Ensure we clear the search if they backspace far enough
                    if(this.value == "") {
                        dtable.search("").draw();
                    }
                    return;
                });
            */
            
            // truncating mechanism
            $('.sentenceLine').click(function() {  
                // truncate all
                $.each($(".sentenceLine"), function() {
                    $(this).addClass('truncate');
                });
                
                // show detail of clicked sentence
                $(this).removeClass('truncate');
                
                // load metadata of related paper
                var id = $(this).attr("data-id");
                
                loadMetaData(id);
            });
            
            // focus on search field
            searchField().focus();
        },
        "oLanguage": { "sSearch": "" }
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
                        html+='						<td><span title="'+this.type+'" data-protein="'+data.literal.slice(this.start,this.end)+'"><span class="label label-' + this.type.toLowerCase() + '" data-databaseID="'+this.databaseID+'">'+data.literal.slice(this.start,this.end)+'</span></span></td>';
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
                        html+='						<td><span title="'+this.type+'" data-protein="'+data.literal.slice(this.start,this.end)+'"><span class="label label-pattern">'+data.literal.slice(this.start,this.end)+'</span></span></td>';
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
                updateOntologyLinks();
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
            
            // resort table (doesn't work)
            var tr = $('#SentenceGrade_'+data.id).parent().parent();
            var row = $("#sentenceTable").DataTable().row(tr);
            var rowData = row.data();
            rowData["grade"] = data.grade;
            $("#sentenceTable").dataTable().fnSort([[3,'desc']]);
	}
    });
}

function contains(haystack, needle) {
    return (String(haystack).toLowerCase().indexOf(String(needle).toLowerCase()) > -1);
}

// extended filter possibilities
$.fn.dataTableExt.afnFiltering.push(
//$.fn.dataTable.ext.search.push(
    function(settings, data, dataIndex) {
        
        var search = searchField().val();
        var rowData = $("#sentenceTable").DataTable().data()[dataIndex];

        //console.log("Search for " + search + " in " + rowData);
        
        if(contains(rowData.pubmedID, search)) return true;
        if(contains(rowData.literal, search)) return true;
        if(contains(rowData.comment, search)) return true;
        
        for(var i = 0; i < rowData.entities.length; i++) {
            if(contains(rowData.entities[i].type, search)) return true;
            if(contains(rowData.entities[i].name, search)) return true;
            if(contains(rowData.entities[i].software, search)) return true;
            if(contains(rowData.entities[i].comment, search)) return true;
        }
        
        for(var i = 0; i < rowData.interactions.length; i++) {
            if(contains(rowData.interactions[i].type, search)) return true;
            if(contains(rowData.interactions[i].comment, search)) return true;
        }
        
        return false;
    }
);

$(function() {
    populateSentenceList();
    addGradeDialogButtonOnClickListener();
});