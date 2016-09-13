(function () {
    "use strict";
    $(document).ready(function() {
        if ($('select').is('#active_filter')){
            var page_size = parseInt($('select').attr("value"));
            var table = $('table').dataTable(
                {   "pageLength" : page_size,
                    "search": {
                                "caseInsensitive": false
                              },
                    "ordering": false
                });
            $('.dataTables_filter').hide();
            $('#active_filter').prop('selectedIndex',0);
            $('#active_filter').on('change', function() {
                if (this.value !== "All") {
                    table.fnFilter( $(this).val());
                }
                else {
                    table.fnFilter("");
                }
            });
        }
    });
})();
