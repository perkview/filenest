from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('features/', views.features, name="features"),
    path('pricing/', views.pricing, name="pricing"),
    path('contact/', views.contact, name="contact"),
    path('login/', views.login, name="login"),
    path('sign/', views.sign, name="sign"),
    path('about/', views.about, name="about"),
    path('policy/', views.policy, name="policy"),
    path('terms/', views.terms, name="terms"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('subscription/', views.subscription, name='subscription'),
    path("send_contact/", views.send_contact, name="send_contact"),
    path("process-selected/<int:doc_id>/", views.process_selected, name="process_selected"),
    path('logout/', views.custom_logout, name='logout'),
    path('settings/', views.settings_page, name='settings_page'),


    path('notifications/', views.home, name='notifications'),
    path('pdf/<int:pdf_id>/view/', views.home, name='view_pdf'),
    path('pdf/<int:pdf_id>/download/', views.home, name='download_pdf'),
    path('subscribe/<str:plan>/', views.home, name='subscribe'),
]
