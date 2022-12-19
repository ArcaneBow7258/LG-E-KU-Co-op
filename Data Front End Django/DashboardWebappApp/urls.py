from django.contrib import admin
from django.urls import path, include
from . import views
#home is a lie. there is not home. just plant_puage
#At one point i need to clean this out and organize... - Alvin
#urlpatterns = [
#    path('', views.searchPage, name="home"),
#    path('chart/<type>?//$',views.chartPage, name="chart")
#]



urlpatterns = [
    path('', views.searchPage, name="home"),
    path('preprocess', views.preprocess, name="preprocess"),
    path('getloads', views.getLoads, name="getloads"),
    path('downloadCSV', views.downloadCSV, name='downloadCSV'),
    path('filteredTagData', views.filteredTagData, name="filteredTagData"),
    path('timeSeries', views.timeSeries, name ="timeSeries"),
    path('searchPage', views.searchPage, name = "searchPage"),
    path('advancedSearch', views.advancedSearch, name = "advancedSearch"),
    path('trends', views.trends, name = "trends"),
    path('requestPage', views.requestPage, name = 'requestPage'),
    path('requestRequests', views.requestRequests, name = 'requestRequests'),
    path('newRequest', views.newRequest, name = 'newRequest'),
    path('explore', views.explore, name = "explore"),
    path('aboveBelow', views.aboveBelow, name = "aboveBelow"),
    path('persistTags', views.persistTags, name = "persistTags"),
    path('sessionTags', views.sessionTags, name = "sessionTags"),
    path('useTagSet', views.useTagSet, name = "useTagSet"),
    path('saveTagSet', views.saveTagSet, name = "saveTagSet"),
    path('getTagSet', views.getTagSet, name = "getTagSet"),
	path('tagGetCol', views.tagGetCol, name ="tagGetCol"),
    path('filteredTagDataNew', views.filteredTagDataNew, name = "filteredTagDataNew"),
]