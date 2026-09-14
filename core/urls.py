from django.urls import path, include
from . import views
from django.contrib import admin
from django.contrib.auth import views as auth_views

urlpatterns = [ 
    path('', views.home, name='home'), 
    path('tarefa/<int:pk>/concluir', views.concluir_tarefa, name='concluir_tarefa'),
    path('tarefa/<int:pk>/deletar', views.deletar_tarefa, name='deletar_tarefa'),
    # path('admin/', admin.site.urls),
    # path('', include('core.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'),name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register')

]
