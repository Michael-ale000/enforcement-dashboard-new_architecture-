from django.urls import path
from . import views

urlpatterns = [
    path('', views.arrests_dashboard, name='home'),
    path('ice-arrests/', views.arrests_dashboard, name='arrests_dashboard'),
    path('documentation/', views.documentation, name='documentation'),
    path('detainers/', views.detainers_dashboard, name='detainers'),
    path('detentions/', views.detentions_dashboard, name='detentions'),
    path('encounters/', views.encounters_dashboard, name='encounters'),
    path('removals/', views.removals_dashboard, name='removals'),
]
