from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.db.models import Q, Avg
from django.contrib.auth import get_user_model
from django.utils import formats
from itertools import chain
from authors.models import Author
from PIL import Image
from datetime import datetime
from reviews.models import Review
from .models import Resource, Keyword, Category, ApprovedResources, SavedResources, Theme, Category, ResourcesGrouped, ResourcePermission
from .forms import ResourceForm, ResourcePermissionForm
import random

User = get_user_model()

def resources(request):
    resources = Resource.objects.all().order_by('id')
    approvedResources = ApprovedResources.objects.all().values_list('resource_id',flat=True)
    user = request.user
    savedResources = None
    savedResources = SavedResources.objects.all().filter(user_id=user.id).values_list('resource_id',flat=True)
    languagesWithContent = Resource.objects.all().values_list('inLanguage',flat=True).distinct()
    themes = Theme.objects.all()
    categories = Category.objects.all()
    filters = {'keywords': '', 'language': ''}

    if request.GET.get('keywords'):
        resources = resources.filter( Q(name__icontains = request.GET['keywords'])  |
                                    Q(keywords__keyword__icontains = request.GET['keywords']) ).distinct()
        filters['keywords'] = request.GET['keywords']

    resources = applyFilters(request, resources)
    filters = setFilters(request, filters)   
    
    resources = resources.filter(~Q(hidden=True))

    resourcesTop = resources.filter(featured=True)
    resourcesTopIds = list(resourcesTop.values_list('id',flat=True))
    resources = resources.exclude(id__in=resourcesTopIds)

    # Ordering
    if request.GET.get('orderby'):
        orderBy = request.GET.get('orderby')
        if("id" in orderBy or "theme" in orderBy):
            resources=resources.order_by(request.GET['orderby'])
        else:
            reviews = Review.objects.filter(content_type=ContentType.objects.get(model="resource"))    
            reviews = reviews.values("object_pk", "content_type").annotate(avg_rating=Avg('rating')).order_by(orderBy).values_list('object_pk',flat=True)
            reviews = list(reviews)
            resourcesVoted = []
            for r in reviews:
                rsc = get_object_or_404(Resource, id=r)
                if rsc in resources:
                    resourcesVoted.append(rsc)

            resources = resources.exclude(id__in=reviews)
            if(orderBy == "avg_rating"):
                resources = list(resources) + list(resourcesVoted)
            else:
                resources = list(resourcesVoted) + list(resources)

        filters['orderby']=request.GET['orderby']
    else:
        resources=resources.order_by('-id')

    # Pin resources to top
    resources = list(resourcesTop) + list(resources)

    paginator = Paginator(resources, 9)
    page = request.GET.get('page')
    resources = paginator.get_page(page)

    return render(request, 'resources.html', {'resources':resources, 'approvedResources': approvedResources,
    'savedResources': savedResources, 'filters': filters, 'settings': settings, 'languagesWithContent': languagesWithContent, 'themes':themes, 'categories': categories})


@login_required(login_url='/login')
def new_resource(request):
    choices = list(Keyword.objects.all().values_list('keyword',flat=True))
    choices = ", ".join(choices)
    authorsCollection = list(Author.objects.all().values_list('author',flat=True))
    authorsCollection = ", ".join(authorsCollection)
    form = ResourceForm(initial={'choices': choices, 'authorsCollection': authorsCollection})
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            images = []
            image1_path = saveImage(request, form, 'image1','1')
            image2_path = saveImage(request, form, 'image2','2')
            images.append(image1_path)
            images.append(image2_path)
            form.save(request, images)
            messages.success(request, "Resource uploaded with success!")
            return redirect('/resources')

    return render(request, 'new_resource.html', {'form': form, 'settings': settings})


def resource(request, pk):
    resource = get_object_or_404(Resource, id=pk)
    user = request.user
    users = getOtherUsers(resource.creator)
    cooperators = getCooperatorsEmail(pk)
    if resource.hidden and ( user.is_anonymous or (user != resource.creator and not user.is_staff and not user.id in getCooperators(pk))):
        return redirect('../resources', {})
    permissionForm = ResourcePermissionForm(initial={'usersCollection':users, 'selectedUsers': cooperators})
    savedResources = SavedResources.objects.all().filter(user_id=user.id).values_list('resource_id',flat=True) #TODO: Only ask for the resource
    approvedResources = ApprovedResources.objects.all().values_list('resource_id',flat=True)
    return render(request, 'resource.html', {'resource':resource, 'savedResources':savedResources, 'approvedResources':approvedResources,
        'cooperators': getCooperators(pk), 'permissionForm': permissionForm})


def editResource(request, pk):
    resource = get_object_or_404(Resource, id=pk)
    user = request.user
    cooperators = getCooperators(pk)
    if user != resource.creator and not user.is_staff and not user.id in cooperators:
        return redirect('../resources', {})

    users = getOtherUsers(resource.creator)
    cooperators = getCooperatorsEmail(pk)
    permissionForm = ResourcePermissionForm(initial={'usersCollection':users, 'selectedUsers': cooperators})

    keywordsList = list(resource.keywords.all().values_list('keyword', flat=True))
    keywordsList = ", ".join(keywordsList)
    choices = list(Keyword.objects.all().values_list('keyword',flat=True))
    choices = ", ".join(choices)
    selectedAuthors = list(resource.authors.all().values_list('author',flat=True))
    selectedAuthors = ", ".join(selectedAuthors)
    authorsCollection = list(Author.objects.all().values_list('author',flat=True))
    authorsCollection = ", ".join(authorsCollection)

    curatedGroups = list(ResourcesGrouped.objects.all().filter(resource_id=pk).values_list('group_id', flat=True))

    form = ResourceForm(initial={
        'name':resource.name, 'abstract': resource.abstract, 'image1': resource.image1, 'image2': resource.image2,'resource_DOI': resource.resourceDOI,
        'withImage1': (True, False)[resource.image1 == ""],'withImage2': (True, False)[resource.image2 == ""],
        'url': resource.url,'license': resource.license, 'choices': choices, 'theme': resource.theme.all,
        'audience' : resource.audience.all, 'publisher': resource.publisher, 'year_of_publication': resource.datePublished,
        'authors': resource.authors.all, 'selectedAuthors': selectedAuthors, 'authorsCollection': authorsCollection,
        'author_email': resource.author_email, 'choicesSelected':keywordsList,
        'category': getCategory(resource.category), 'categorySelected': resource.category.id
    })

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            images = []
            image1_path = saveImage(request, form, 'image1','1')
            image2_path = saveImage(request, form, 'image2','2')
            images.append(image1_path)
            images.append(image2_path)
            form.save(request, images)
            messages.success(request, "Resource uploaded with success!")

            return redirect('/resource/'+ str(pk))

    return render(request, 'editResource.html', {'form': form, 'resource': resource, 'curatedGroups': curatedGroups,
     'user': user, 'settings': settings, 'permissionForm': permissionForm })

def deleteResource(request, pk):
    obj = get_object_or_404(Resource, id=pk)
    if request.user == obj.creator or request.user.is_staff or request.user.id in getCooperators(pk):
        obj.delete()
        reviews = Review.objects.filter(content_type=ContentType.objects.get(model="resource"), object_pk=pk)
        for r in reviews:
            r.delete()
    return redirect('resources')

def resources_autocomplete(request):
    resources = preFilteredResources(request)
    if request.GET.get('q'):
        text = request.GET['q']
        resourceNames = resources.filter( Q(name__icontains = text) ).distinct()
        resourceKeywords = resources.filter( Q(keywords__keyword__icontains = text) ).distinct()
        rsc_names = resourceNames.values_list('name',flat=True).distinct()
        keywords = resourceKeywords.values_list('keywords__keyword',flat=False).distinct()
        keywords = Keyword.objects.filter(keyword__in = keywords).values_list('keyword',flat=True).distinct()
        report = chain(rsc_names, keywords)
        json = list(report)
        return JsonResponse(json, safe=False)
    else:
        return HttpResponse("No cookies")

def getRscNamesKeywords(text):
    rsc_names = Resource.objects.filter(name__icontains=text).values_list('name',flat=True).distinct()
    keywords = Keyword.objects.filter(keyword__icontains=text).values_list('keyword',flat=True).distinct()
    report = chain(rsc_names, keywords)
    return report

def getOtherUsers(creator):
    users = list(User.objects.all().exclude(is_superuser=True).exclude(id=creator.id).values_list('email',flat=True))
    users = ", ".join(users)
    return users

def getCooperators(resourceID):
    users = list(ResourcePermission.objects.all().filter(resource_id=resourceID).values_list('user',flat=True))
    return users

def getCooperatorsEmail(resourceID):
    users = getCooperators(resourceID)
    cooperators = ""
    for user in users:
        userObj = get_object_or_404(User, id=user)
        cooperators += userObj.email + ", "
    return cooperators

def clearFilters(request):
    return redirect ('resources')

def saveImage(request, form, element, ref):
    image_path = ''
    filepath = request.FILES.get(element, False)
    withImage = form.cleaned_data.get('withImage' + ref)
    if (filepath):
        x = form.cleaned_data.get('x' + ref)
        y = form.cleaned_data.get('y' + ref)
        w = form.cleaned_data.get('width' + ref)
        h = form.cleaned_data.get('height' + ref)
        photo = request.FILES[element]
        image = Image.open(photo)
        cropped_image = image.crop((x, y, w+x, h+y))
        if(ref == '2'):
            resized_image = cropped_image.resize((1100, 400), Image.ANTIALIAS)
        else:
            resized_image = cropped_image.resize((600, 400), Image.ANTIALIAS)
        _datetime = formats.date_format(datetime.now(), 'Y-m-d_hhmmss')
        random_num = random.randint(0, 1000)
        image_path = "media/images/" + _datetime + '_' + str(random_num) + '_' + photo.name
        resized_image.save(image_path)
        image_path = '/' + image_path
    elif withImage:
            image_path = '/'
    else:
        image_path = ''
    return image_path

def preFilteredResources(request):
    resources = Resource.objects.all().order_by('id')
    return applyFilters(request, resources)

def applyFilters(request, resources):
    approvedResources = ApprovedResources.objects.all().values_list('resource_id',flat=True)

    if request.GET.get('language'):
        resources = resources.filter(inLanguage = request.GET['language'])
    if request.GET.get('license'):
        resources = resources.filter(license__icontains = request.GET['license'])
    if request.GET.get('theme'):
        resources = resources.filter(theme = request.GET['theme'])
    if request.GET.get('category'):
        resources = resources.filter(category = request.GET['category'])
    if request.GET.get('approvedCheck'):
        if request.GET['approvedCheck'] == 'On':
            resources = resources.filter(id__in=approvedResources)
        if request.GET['approvedCheck'] == 'Off':
            resources = resources.exclude(id__in=approvedResources)
        if request.GET['approvedCheck'] == 'All':
            resources = resources
    else:
        resources = resources.filter(id__in=approvedResources)

    return resources

def setFilters(request, filters):
    if request.GET.get('language'):
        filters['language'] = request.GET['language']
    if request.GET.get('license'):
        filters['license'] = request.GET['license']
    if request.GET.get('theme'):
        filters['theme'] = int(request.GET['theme'])
    if request.GET.get('category'):
        filters['category'] = int(request.GET['category'])
    if request.GET.get('approvedCheck'):
        filters['approvedCheck'] = request.GET['approvedCheck']
    return filters


def get_sub_category(request):
    category = request.GET.get("category")
    options = '<select id="id_subcategory" class="select form-control">'
    response = {}

    if category:
        sub_categories = Category.objects.filter(parent=category)
        sub_categories = sub_categories.values_list("id","text")
        tupla_sub_categories = tuple(sub_categories)
        if tupla_sub_categories:
            for sub_category in tupla_sub_categories:
                options += '<option value = "%s">%s</option>' % (
                    sub_category[0],
                    sub_category[1]
                )
            options += '</select>'
            response['sub_categories'] = options
        else:
            response['sub_categories'] = '<select id="id_subcategory" class="select form-control" disabled></select>'
    else:
        response['sub_categories'] = '<select id="id_subcategory" class="select form-control" disabled></select>'
    return JsonResponse(response)


def getCategory(category):
    if category.parent:
            return category.parent
    else:
        return category

@staff_member_required()
def setApprovedRsc(request):
    response = {}
    id = request.POST.get("resource_id")
    approved = request.POST.get("approved")
    setResourceApproved(id, approved)
    return JsonResponse(response, safe=False)

def setResourceApproved(id, approved):
    approved= False if approved in ['False','false','0'] else True
    aResource = get_object_or_404(Resource, id=id)
    if approved == True:
        #Insert        
        ApprovedResources.objects.get_or_create(resource=aResource)
    else:
        #Delete
        try:
            obj = ApprovedResources.objects.get(resource_id=id)
            obj.delete()
        except ApprovedResources.DoesNotExist:
            print("Does not exist this approved resource")

def setSavedResource(request):
    response = {}
    resourceId = request.POST.get("resource_id")
    userId = request.POST.get("user_id")
    save = request.POST.get("save")
    saveResource(resourceId, userId, save)
    return JsonResponse(response, safe=False)


def saveResource(resourceId, userId, save):
    save= False if save in ['False','false','0'] else True
    fResource = get_object_or_404(Resource, id=resourceId)
    fUser = get_object_or_404(User, id=userId)
    if save == True:
        #Insert
        savedResource = SavedResources.objects.get_or_create(resource=fResource, user=fUser)
    else:
        #Delete
        try:            
            obj = SavedResources.objects.get(resource_id=resourceId,user_id=userId)
            obj.delete()
        except SavedResources.DoesNotExist:
            print("Does not exist this resource saved")


@staff_member_required()
def setHiddenResource(request):
    response = {}
    id = request.POST.get("resource_id")
    hidden = request.POST.get("hidden")
    setResourceHidden(id, hidden)
    return JsonResponse(response, safe=False)

def setResourceHidden(id, hidden): 
    resource = get_object_or_404(Resource, id=id)
    resource.hidden = False if hidden in ['False','false','0'] else True
    resource.save()

@staff_member_required()
def setFeaturedResource(request):
    response = {}
    id = request.POST.get("resource_id")
    featured = request.POST.get("featured")
    setResourceFeatured(id, featured)
    return JsonResponse(response, safe=False)

def setResourceFeatured(id, featured):
    resource = get_object_or_404(Resource, id=id)
    resource.featured = featured
    resource.featured = False if featured in ['False','false','0'] else True
    resource.save()

def allowUserResource(request):
    response = {}
    resourceId = request.POST.get("resource_id")
    users = request.POST.get("users")
    resource = get_object_or_404(Resource, id=resourceId)

    if request.user != resource.creator and not request.user.is_staff:
        #TODO return JsonResponse with error code
        return redirect('../resources', {})

    #Delete all
    objs = ResourcePermission.objects.all().filter(resource_id=resourceId)
    if(objs):
        for obj in objs:
            obj.delete()

    #Insert all    
    users = users.split(',')
    for user in users:
        fUser = User.objects.filter(email=user)[:1].get()
        resourcePermission = ResourcePermission(resource=resource, user=fUser)
        resourcePermission.save()

    return JsonResponse(response, safe=False)

def resource_review(request, pk):
    return render(request, 'resource_review.html', {'resourceID': pk})
