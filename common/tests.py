import unicodedata
from random import choice

import pytest
from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from hypothesis import Verbosity, assume, given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import from_field, from_form

from common.forms import (
    DEPARTMENTS,
    EMAIL_ALLOW_REGEX,
    UNIVERSITIES,
    ProfileForm,
    SignUpForm,
    UserForm,
)
from common.models import UserProfile


def get_affilitaion(email):
    return email.split("@")[1].split(".")[-2].lower()


@st.composite
def input_form(
    draw,
    email=st.emails(domains=st.from_regex(EMAIL_ALLOW_REGEX, fullmatch=True)),
    name=st.text(min_size=3, max_size=20),
    surname=st.text(min_size=3, max_size=20),
    affiliation_getter=get_affilitaion,
    why_account_needed=st.text(min_size=10, max_size=100),
    department=st.sampled_from(DEPARTMENTS),
):
    mail = draw(email)
    pwd = draw(st.text(min_size=8).map(make_password))
    department = draw(department)
    affiliation = affiliation_getter(mail)
    name_ = unicodedata.normalize("NFKD", draw(name).replace("\x00", "\uFFFD"))
    surname_ = unicodedata.normalize("NFKD", draw(surname).replace("\x00", "\uFFFD"))
    why_account_needed = draw(why_account_needed)
    if why_account_needed is not None:
        why_account_needed = unicodedata.normalize("NFKD", why_account_needed.replace("\x00", "\uFFFD"))

    user_form = UserForm(
        {
            "first_name": name_,
            "last_name": surname_,
            "email": mail,
            "password1": pwd,
            "password2": pwd,
            "username": mail,
        }
    )

    profile_form = ProfileForm(
        {
            "why_account_needed": why_account_needed,
            "department": department,
            "affiliation": affiliation,
        }
    )

    form = SignUpForm(user=user_form, profile=profile_form)
    return form


@pytest.mark.pass_validation
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
@given(form=input_form())
@settings(verbosity=Verbosity.verbose, max_examples=30)
def test_pass_validation(form):

    UserProfile.objects.all().delete()
    User.objects.all().delete()
    is_val = form.is_valid()
    assert hasattr(form.user, "cleaned_data")
    assert hasattr(form.profile, "cleaned_data")
    assert is_val, (form.user.errors, form.profile.errors)
    profile = form.save()
    assert profile.user.username == profile.user.email


@pytest.mark.django_db
@given(
    form=input_form(
        email=st.emails().filter(lambda x: get_affilitaion(x) not in [unis[0] for unis in UNIVERSITIES]),
        affiliation_getter=lambda x: "other",
        why_account_needed=st.text(min_size=10, max_size=100),
    )
)
def test_pass_validation_other_email_request_account(form):
    is_val = form.is_valid()
    assert hasattr(form.user, "cleaned_data")
    assert hasattr(form.profile, "cleaned_data")
    assert is_val, form.user.errors


@pytest.mark.django_db
@given(
    form=input_form(
        affiliation_getter=lambda x: choice(
            [unis[0] for unis in UNIVERSITIES if unis[0] not in (get_affilitaion(x), "other")]
        )
    )
)
def test_invalid_input_affiliation_ne_email(form):
    is_val = form.is_valid()
    assert hasattr(form.user, "cleaned_data")
    assert hasattr(form.profile, "cleaned_data")
    assert not is_val
    assert {"affiliation": ["Email affiliation is different from selected"]} == form.profile.errors


@pytest.mark.django_db
@given(form=input_form(affiliation_getter=lambda x: "other"))
def test_invalid_input_affilitaion_is_other(form):
    is_val = form.is_valid()
    assert hasattr(form.user, "cleaned_data")
    assert hasattr(form.profile, "cleaned_data")
    assert not is_val
    assert {"affiliation": ["You are required to select your affiliation"]} == form.profile.errors


@pytest.mark.django_db
@given(form=input_form(department=st.sampled_from(["", None])))
def test_invalid_input_department_is_empty(form):
    is_val = form.is_valid()
    assert hasattr(form.profile, "cleaned_data")
    assert not is_val
    assert {"department": ["You are required to select your department"]} == form.profile.errors


@pytest.mark.django_db
@given(
    form=input_form(
        email=st.emails().filter(lambda x: get_affilitaion(x) not in [unis[0] for unis in UNIVERSITIES]),
        affiliation_getter=lambda x: "other",
        why_account_needed=st.sampled_from(["", None]),
    )
)
@settings(verbosity=Verbosity.verbose)
def test_fail_validation_other_email_request_account_field_empty(form):
    is_val = form.is_valid()
    assert not is_val, (form.user.errors, form.profile.errors)
    assert {"why_account_needed": ["Please describe why do you need an account"]} == form.profile.errors


@pytest.mark.django_db
@given(
    form=input_form(
        email=st.emails().filter(lambda x: get_affilitaion(x) not in [unis[0] for unis in UNIVERSITIES]),
        affiliation_getter=lambda x: choice([unis[0] for unis in UNIVERSITIES if unis[0] != "other"]),
    )
)
def test_fail_validation_other_email_affiliation_selected(form):
    is_val = form.is_valid()
    assert not is_val, (form.user.errors, form.profile.errors)
    assert {
        "email": [
            "Email is not from Swedish University. \n"
            "Please select 'Other' in affiliation or use your University email"
        ]
    } == form.user.errors
