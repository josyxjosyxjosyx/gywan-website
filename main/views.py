from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
import stripe
import json
from .models import Event, Story, BlogPost, Resource, Donation, Contact, Newsletter, ImpactStory, ImpactStat, Comment, TeamMember, Supporter
from .forms import ContactForm, DonationForm, NewsletterForm
from django.contrib.contenttypes.models import ContentType


def our_team_view(request):
    team_members = TeamMember.objects.filter(is_active=True).order_by('created_at')
    supporters = Supporter.objects.filter(is_active=True).order_by('created_at')
    return render(request, 'about/team.html', {
        'team_members': team_members,
        'supporters': supporters
    })


class HomeView(TemplateView):
    """Homepage with featured content"""
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get upcoming events (events with date >= today)
        context['upcoming_events'] = Event.objects.filter(
            date__gte=timezone.now(),
            is_active=True
        ).order_by('date')[:6]
        
        # Get recent stories
        context['recent_stories'] = Story.objects.filter(
            is_active=True
        ).order_by('-created_at')[:6]
        
        # Get recent resources
        context['recent_resources'] = Resource.objects.filter(
            is_active=True
        ).order_by('-created_at')[:6]
        
        context['newsletter_form'] = NewsletterForm()
        context['impact_stats'] = ImpactStat.objects.filter(is_active=True)
        return context



from .models import TeamMember

class AboutView(TemplateView):
    """About page with organization information"""
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_members'] = TeamMember.objects.filter(is_active=True)
        return context


class ContactView(CreateView):
    """Contact form view"""
    model = Contact
    form_class = ContactForm
    template_name = 'contact.html'
    success_url = '/contact/'
    
    def form_valid(self, form):
        # Send email notification
        try:
            send_mail(
                f'New Contact Form Submission: {form.cleaned_data["subject"]}',
                f'Name: {form.cleaned_data["name"]}\nEmail: {form.cleaned_data["email"]}\n\nMessage:\n{form.cleaned_data["message"]}',
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        messages.success(self.request, 'Thank you for your message! We will get back to you soon.')
        return super().form_valid(form)


class DonateView(TemplateView):
    """Donation page with Stripe integration"""
    template_name = 'donate.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        context['donation_form'] = DonationForm()
        impact_stories = ImpactStory.objects.order_by('-created_at')[:4]
        context['impact_stories'] = impact_stories
        return context


class ProcessDonationView(TemplateView):
    """Process Stripe donation"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            
            # Configure Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(float(data['amount']) * 100),  # Convert to cents
                currency='usd',
                metadata={
                    'donor_name': data['donor_name'],
                    'donor_email': data['donor_email'],
                    'donation_type': data['donation_type']
                }
            )
            
            # Create donation record
            donation = Donation.objects.create(
                amount=data['amount'],
                donation_type=data['donation_type'],
                donor_name=data['donor_name'],
                donor_email=data['donor_email'],
                message=data.get('message', ''),
                is_anonymous=data.get('is_anonymous', False),
                stripe_payment_id=intent.id
            )
            
            return JsonResponse({
                'success': True,
                'client_secret': intent.client_secret,
                'donation_id': donation.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class EventListView(ListView):
    """List view for events"""
    model = Event
    template_name = 'events/list.html'
    context_object_name = 'events'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_comments'] = Comment.objects.order_by('-created_at')[:10]
        return context

    def get_queryset(self):
        queryset = Event.objects.filter(is_active=True)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query)
            )
        return queryset

    def post(self, request, *args, **kwargs):
        comment_text = request.POST.get('comment')
        if comment_text:
            Comment.objects.create(text=comment_text)
        return redirect(request.path)


class EventDetailView(DetailView):
    """Detail view for individual events"""
    model = Event
    template_name = 'events/detail.html'
    context_object_name = 'event'
    
    def get_queryset(self):
        return Event.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        content_type = ContentType.objects.get_for_model(obj)
        context['recent_comments'] = Comment.objects.filter(content_type=content_type, object_id=obj.id).order_by('-created_at')[:10]
        return context

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        comment_text = request.POST.get('comment')
        name = request.POST.get('name')
        email = request.POST.get('email')
        if comment_text and name and email:
            content_type = ContentType.objects.get_for_model(obj)
            Comment.objects.create(text=comment_text, name=name, email=email, content_type=content_type, object_id=obj.id)
        return redirect(request.path)


class StoryListView(ListView):
    """List view for success stories"""
    model = Story
    template_name = 'stories/list.html'
    context_object_name = 'stories'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_comments'] = Comment.objects.order_by('-created_at')[:10]
        return context

    def get_queryset(self):
        queryset = Story.objects.filter(is_active=True)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(author__icontains=query)
            )
        return queryset

    def post(self, request, *args, **kwargs):
        comment_text = request.POST.get('comment')
        if comment_text:
            Comment.objects.create(text=comment_text)
        return redirect(request.path)


class StoryDetailView(DetailView):
    """Detail view for individual stories"""
    model = Story
    template_name = 'stories/detail.html'
    context_object_name = 'story'
    
    def get_queryset(self):
        return Story.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        content_type = ContentType.objects.get_for_model(obj)
        context['recent_comments'] = Comment.objects.filter(content_type=content_type, object_id=obj.id).order_by('-created_at')[:10]
        return context

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        comment_text = request.POST.get('comment')
        name = request.POST.get('name')
        email = request.POST.get('email')
        if comment_text and name and email:
            content_type = ContentType.objects.get_for_model(obj)
            Comment.objects.create(text=comment_text, name=name, email=email, content_type=content_type, object_id=obj.id)
        return redirect(request.path)


class BlogListView(ListView):
    """List view for blog posts"""
    model = BlogPost
    template_name = 'blog/list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_comments'] = Comment.objects.order_by('-created_at')[:10]
        return context

    def get_queryset(self):
        queryset = BlogPost.objects.filter(published=True, is_active=True)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(tags__icontains=query)
            )
        return queryset

    def post(self, request, *args, **kwargs):
        comment_text = request.POST.get('comment')
        if comment_text:
            Comment.objects.create(text=comment_text)
        return redirect(request.path)


class BlogDetailView(DetailView):
    """Detail view for individual blog posts"""
    model = BlogPost
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return BlogPost.objects.filter(published=True, is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        content_type = ContentType.objects.get_for_model(obj)
        context['recent_comments'] = Comment.objects.filter(content_type=content_type, object_id=obj.id).order_by('-created_at')[:10]
        return context

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        comment_text = request.POST.get('comment')
        name = request.POST.get('name')
        email = request.POST.get('email')
        if comment_text and name and email:
            content_type = ContentType.objects.get_for_model(obj)
            Comment.objects.create(text=comment_text, name=name, email=email, content_type=content_type, object_id=obj.id)
        return redirect(request.path)


class ResourceListView(ListView):
    """List view for resources"""
    model = Resource
    template_name = 'resources/list.html'
    context_object_name = 'resources'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_comments'] = Comment.objects.order_by('-created_at')[:10]
        return context

    def get_queryset(self):
        queryset = Resource.objects.filter(is_active=True)
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def post(self, request, *args, **kwargs):
        comment_text = request.POST.get('comment')
        if comment_text:
            Comment.objects.create(text=comment_text)
        return redirect(request.path)


def newsletter_subscribe(request):
    """Handle newsletter subscription via AJAX"""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Thank you for subscribing!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .models import Resource

@csrf_exempt
def track_download(request, resource_id):
    if request.method == 'POST':
        try:
            resource = Resource.objects.get(pk=resource_id)
            resource.download_count = resource.download_count + 1
            resource.save(update_fields=['download_count'])
            return JsonResponse({'success': True, 'download_count': resource.download_count})
        except Resource.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Resource not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)
