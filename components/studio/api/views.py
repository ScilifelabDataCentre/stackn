import requests
import json
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics
from deployments.helpers import deploy_model


from .serializers import Model, MLModelSerializer, Report, ReportSerializer, \
    ReportGenerator, ReportGeneratorSerializer, Project, ProjectSerializer, \
    DeploymentInstance, DeploymentInstanceSerializer, DeploymentDefinition, \
    DeploymentDefinitionSerializer


class ModelList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = MLModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    def get_queryset(self):
        """
        This view should return a list of all the models
        for the currently authenticated user.
        """
        current_user = self.request.user
        return Model.objects.filter(project__owner__username=current_user)

class DeploymentDefinitionList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeploymentDefinitionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    
    def get_queryset(self):
        """
        This view should return a list of all the deployments
        for the currently authenticated user.
        """
        current_user = self.request.user
        return DeploymentDefinition.objects.filter(project__owner__username=current_user)

class DeploymentInstanceList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeploymentInstanceSerializer

    def get_queryset(self):
        """
        This view should return a list of all the deployments
        for the currently authenticated user.
        """
        current_user = self.request.user
        return DeploymentInstance.objects.filter(model__project__owner__username=current_user)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def build_instance(self, request):
        print('starting build process...')
        deployment_name = request.data['name']
        instance = DeploymentInstance.objects.get(name=deployment_name)
        print(instance)
        deploy_model(instance)
        return HttpResponse('ok', status=200)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def predict(self, request):
        print('predicting...')
        name = request.query_params['name']
        version = request.query_params['version']
        current_user = self.request.user
        instance = DeploymentInstance.objects.get(model__project__owner__username=current_user,
                                                  name=name,
                                                  version=version)
        internal_endpoint = 'http://{}-{}/v1/models/model:predict'.format(instance.name, instance.version)
        r = requests.post(internal_endpoint, json=request.data)
        print(r.text)
        return HttpResponse(r.text, status=r.status_code)

class ReportList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReportSerializer

    def get_queryset(self):
        """
        This view should return a list of all the reports
        for the currently authenticated user.
        """
        current_user = self.request.user
        return Report.objects.filter(generator__project__owner__username=current_user)


class ReportGeneratorList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReportGeneratorSerializer

    def get_queryset(self):
        """
        This view should return a list of all the report generators
        for the currently authenticated user.
        """
        current_user = self.request.user
        return ReportGenerator.objects.filter(project__owner__username=current_user)


class ProjectList(generics.ListAPIView, GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin,
                  ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']

    def get_queryset(self):
        """
        This view should return a list of all the projects
        for the currently authenticated user.
        """
        current_user = self.request.user
        return Project.objects.filter(owner__username=current_user)
