function move_remove_all(where,list_id)
{
	if (where == 'right')
	{
		$('#' + list_id + ' #multivalfrom').find('option').each(function(){
			var optionval = '<option value="'+$(this).attr("value")+'">'+$(this).html()+'</option>';
			$('#' + list_id).find('#multivalto').append(optionval);
		});
		$('#' + list_id + ' #multivalfrom').html('');
	}
	else if (where == 'left')
	{
		$('#' + list_id + ' #multivalto').find('option').each(function(){
			var optionval = '<option value="'+$(this).attr("value")+'">'+$(this).html()+'</option>';
			$('#' + list_id).find('#multivalfrom').append(optionval);
		});
		$('#' + list_id + ' #multivalto').html('');
	}
}
function top_bottom(where,list_id)
{
	var selected = $('#' + list_id + ' #multivalto').val();
    var selected_elems = $('#' + list_id + ' #multivalto :selected')
    var selected_txts = $.map( selected_elems, function(value, index) {
        return $(value).text()
    });

	var appendvalue = '';
	for (i=0;i<selected.length;i++)
	{
		appendvalue += '<option value="'+selected[i]+'">'+selected_txts[i]+'</option>';
		$('#' + list_id + ' #multivalto option[value="'+selected[i]+'"]').remove();
	}
	if (where == 'top')
	{
		$('#' + list_id + ' #multivalto').prepend(appendvalue);
	}
	else if (where == 'bottom')
	{
		$('#' + list_id + ' #multivalto').append(appendvalue);
	}
};
function up_down(where,list_id)
{
	var $op = $('#' + list_id + ' #multivalto option:selected');
	if($op.length)
	{
		if(where == 'up')
		{
			$op.first().prev().before($op)
		}
		else if (where == 'down')
		{
			$op.last().next().after($op);
		}	
	}		
}
function move_remove(where,list_id)
{
	if (where == 'right')
	{
		var selected = $('#' + list_id).find('#multivalfrom').val();
        var selected_elems = $('#' + list_id + ' #multivalfrom :selected')
        var selected_txts = $.map( selected_elems, function(value, index) {
            return $(value).text()
        });
		var appendvalue = ''
		for (i=0;i<selected.length;i++)
		{
			appendvalue += '<option value="'+selected[i]+'">'+selected_txts[i]+'</option>';
			$('#' + list_id).find('#multivalfrom option[value="'+selected[i]+'"]').remove();
		}
		$('#' + list_id).find('#multivalto').append(appendvalue);
	}
	else if (where == 'left')
	{
		var selected = $('#' + list_id).find('#multivalto').val();
        var selected_elems = $('#' + list_id + ' #multivalto :selected')
        var selected_txts = $.map( selected_elems, function(value, index) {
            return $(value).text()
        });
		var appendvalue = ''
		for (i=0;i<selected.length;i++)
		{
			appendvalue += '<option value="'+selected[i]+'">'+selected_txts[i]+'</option>';
			$('#' + list_id).find('#multivalto option[value="'+selected[i]+'"]').remove();
		}
		$('#' + list_id).find('#multivalfrom').append(appendvalue);			
	}
}
function assign_btn_action(list_id)
{
	$("#" + list_id).find("#top_btn")[ 0 ].onclick = function() {
		top_bottom('top',list_id);
	};
	$("#" + list_id).find("#bottom_btn")[ 0 ].onclick = function() {
		top_bottom('bottom',list_id);
	};
	$("#" + list_id).find("#up_btn")[ 0 ].onclick = function() {
		up_down('up',list_id);
	};
	$("#" + list_id).find("#down_btn")[ 0 ].onclick = function() {
		up_down('down',list_id);
	};
	$("#" + list_id).find("#move_btn")[ 0 ].onclick = function() {
		move_remove('right',list_id);
	};
	$("#" + list_id).find("#remove_btn")[ 0 ].onclick = function() {
		move_remove('left',list_id);
	};
	$("#" + list_id).find("#move_all_btn")[ 0 ].onclick = function() {
		move_remove_all('right',list_id);
	};
	$("#" + list_id).find("#remove_all_btn")[ 0 ].onclick = function() {
		move_remove_all('left',list_id);
	};	
}

function getvalue(list_id)
{
	var values = '';
	$("#" + list_id + " #multivalto").find("option").each(function(){
		values += $(this).html() + ',';
	});
	values = values.substr(0,values.lastIndexOf(','));	
	return values;
}