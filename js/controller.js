'use strict';

/* Controllers */

var phonecatApp = angular.module('ng-app', []);

phonecatApp.controller('TopArtisListCtrl', function($scope, $http) {
  $http.get('/getTopArtist').success(function(data) {
  	console.log(data)
    $scope.artists = data;
  });

});

phonecatApp.controller('TopTagsListCtrl', function($scope, $http) {
  $http.get('/getTopTags').success(function(data) {
  	console.log(data)
    $scope.tags = data;
  });

});

