from django.shortcuts import get_object_or_404, render

from menu.models import Category, FoodItem
from vendor.models import Vendor
from vendor.views import fooditems_by_category
from django.db.models import Prefetch

# Create your views here.
def marketplace(request):
    vendors=Vendor.objects.filter(is_approved=True,user__is_active=True)
    vendors_count=vendors.count()
    context={
        'vendors':vendors,
        'vendors_count': vendors_count,

    }
    return render(request,'marketplace/listings.html',context)
def vendor_details(request,vendor_slug):
    vendor=get_object_or_404(Vendor,vendor_slug=vendor_slug)
    categories = Category.objects.filter(vendor=vendor).prefetch_related(
        Prefetch(
            'fooditems',
            queryset = FoodItem.objects.filter(is_available=True)
        )
    )


    
        
    context={
        "vendor":vendor,
        "categories":categories
    }

    return render(request,"marketplace/vendor_details.html",context)