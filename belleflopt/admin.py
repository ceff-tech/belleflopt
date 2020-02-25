from django.contrib import admin

from belleflopt import models

# Register your models here.


class ModelRunAdmin(admin.ModelAdmin):
    exclude = ('segments',)


admin.site.register(models.ModelRun, ModelRunAdmin)
