from django.shortcuts import render


def home(request):
    return render(request, 'Users/home.html')
