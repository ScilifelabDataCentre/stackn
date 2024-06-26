from apps.forms import (
    CustomAppForm,
    DashForm,
    FilemanagerForm,
    JupyterForm,
    NetpolicyForm,
    RStudioForm,
    ShinyForm,
    TissuumapsForm,
    VolumeForm,
    VSCodeForm,
)
from apps.models import (
    CustomAppInstance,
    DashInstance,
    FilemanagerInstance,
    JupyterInstance,
    NetpolicyInstance,
    RStudioInstance,
    ShinyInstance,
    TissuumapsInstance,
    VolumeInstance,
    VSCodeInstance,
)
from apps.types_.app_registry import AppRegistry
from apps.types_.app_types import ModelFormTuple

APP_REGISTRY = AppRegistry()
APP_REGISTRY.register("jupyter-lab", ModelFormTuple(JupyterInstance, JupyterForm))
APP_REGISTRY.register("rstudio", ModelFormTuple(RStudioInstance, RStudioForm))
APP_REGISTRY.register("vscode", ModelFormTuple(VSCodeInstance, VSCodeForm))
APP_REGISTRY.register("volumeK8s", ModelFormTuple(VolumeInstance, VolumeForm))
APP_REGISTRY.register("netpolicy", ModelFormTuple(NetpolicyInstance, NetpolicyForm))
APP_REGISTRY.register("dashapp", ModelFormTuple(DashInstance, DashForm))
APP_REGISTRY.register("customapp", ModelFormTuple(CustomAppInstance, CustomAppForm))
APP_REGISTRY.register("shinyapp", ModelFormTuple(ShinyInstance, ShinyForm))
APP_REGISTRY.register("shinyproxyapp", ModelFormTuple(ShinyInstance, ShinyForm))
APP_REGISTRY.register("tissuumaps", ModelFormTuple(TissuumapsInstance, TissuumapsForm))
APP_REGISTRY.register("filemanager", ModelFormTuple(FilemanagerInstance, FilemanagerForm))
