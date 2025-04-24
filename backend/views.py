from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages

def static_page(request, page):
    return render(request, f'frontend/pages/{page}/index.html')

def homepage(request):
    return render(request, 'frontend/pages/AppLogin/index.html')  # AppLogin as main page

# Needs to be fixed
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        messages.success(request, "Account created successfully!")
        return redirect('login')

    return render(request, 'register.html')
