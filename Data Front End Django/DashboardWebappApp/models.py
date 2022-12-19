from django.db import models

# Create your models here.
class Account(models.Model):
    number = models.CharField(max_length=50, primary_key=True)
    tags = models.CharField(max_length=1024)
    plants = models.CharField(max_length=1024)
    minTime = models.DateTimeField("Start")
    maxTime = models.DateTimeField("End")
#/Path/To/Tag/Set/Name -> 
class TagSet(models.Model):
    filePath = models.CharField(max_length=512)
    name = models.CharField(max_length= 128)
    fullPath = models.CharField(max_length= 640, primary_key=True)#used for PK
    tags = models.CharField(max_length=1024)
    plants = models.CharField(max_length=1024)
    minTime = models.DateTimeField("Start")
    maxTime = models.DateTimeField("End")
    lastUpdated = models.DateTimeField("Last Updated")
    lastUsed = models.DateTimeField("Last Used", null = True, blank  =True)
    def clean(self):
        self.fullPath = self.filePath + '/' + self.name
    def dict(self):
        return {'filePath': self.filePath,
                'name': self.name,
                'tags': self.tags,
                'plants':self.plants,
                'minTime':self.minTime,
                'maxTime':self.maxTime,
                'lastUpdated':self.lastUpdated,
                'lastUsed':self.lastUsed
            }
    
class TagRequest(models.Model):
    tagName = models.CharField(max_length=128, primary_key=True)
    InitialRequestDate = models.DateField("Initial Request")
    LastRequestDate = models.DateField("Last Request")
    #seenDate = models.DateField("Seen", null = True, blank  =True)
    completedDate =models.DateField("Completed", null = True, blank  =True)
    priority = models.PositiveSmallIntegerField(default = 0)
    
    class Meta:
        ordering = ['-priority', '-InitialRequestDate', '-LastRequestDate']
    
    
    