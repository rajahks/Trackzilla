// Ajax based Autocomplete using the library https://github.com/devbridge/jQuery-Autocomplete
// https://www.devbridge.com/sourcery/components/jquery-autocomplete/

$(function () {
    'use strict';

    $('#q').autocomplete({
    serviceUrl: "/search/autocomplete/",
    minChars: 2,
    dataType: 'json',
    type: 'GET',
    onSelect: function (suggestion) {
      console.log( 'Autocomplete Value:' + suggestion.value + ', data :' + suggestion.data);
    }
  });

  });
