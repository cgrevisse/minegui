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
                
                var stars = "";
                for(var i = 1; i <= this.grade; i++) stars += '<span class="glyphicon glyphicon-star"></span>'
                for(var i = this.grade + 1; i <= MAX_STARS; i++) stars += '<span class="glyphicon glyphicon-star-empty"></span>'
                tr.append($('<td>' + stars +'</td>'))
                
                // TODO: use this.id to open popup and load data from REST interface /sentences/<id>
                tr.append($('<td><button type="button" class="btn btn-warning btn-xs"><span class="glyphicon glyphicon-tasks"></span> Curate</button></td>'));
                
                list.append(tr);
                
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

$(function() {
    populateSentenceList();
});