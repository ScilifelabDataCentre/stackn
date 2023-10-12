from django.conf import settings
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from django.db import transaction

from .forms import SignUpForm, UserForm, ProfileForm


# Create your views here.
class HomeView(TemplateView):
    template_name = "common/landing.html"


class RegistrationCompleteView(TemplateView):
    template_name = "registration/registration_complete.html"


# Sign Up View


class SignUpView(CreateView):
    template_name = "registration/signup.html"
    form_class = UserForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'profile_form' not in context:
            context['profile_form'] = ProfileForm(self.request.POST or None)
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        profile_form = context['profile_form']
        form_ = SignUpForm(user=form, profile=profile_form)
        form_.clean()
        if form_.is_valid():
            form_.save()
            # TODO send email to registered user to confirm email address here
            if settings.INACTIVE_USERS:
                messages.success(self.request, "Account request has been registered! Please wait for admin to approve!")
                redirect_name = "common:success"
            else:
                messages.success(self.request, "Account created successfully!")
                redirect_name = "login"
            return HttpResponseRedirect(reverse_lazy(redirect_name))
        else:
            print(form_.user.errors)  # Print errors to the console or log them
            print(form_.profile.errors)  # Print errors to the console or log them
            return self.form_invalid(form_)

    def form_invalid(self, form: SignUpForm):
        context = self.get_context_data()
        context['form'] = form.user  # The user form
        context['profile_form'] = form.profile  # The profile form
        print(form.user.errors)  # Print errors to the console or log them
        print(form.profile.errors)  # Print errors to the console or log them
        return self.render_to_response(context)
