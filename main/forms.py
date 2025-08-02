from django import forms
from django.core.validators import MinValueValidator
from .models import Contact, Donation, Newsletter


class ContactForm(forms.ModelForm):
    """Contact form with enhanced styling"""
    
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Your Full Name'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
        self.fields['subject'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'What is this about?'
        })
        self.fields['message'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Tell us more about your inquiry...',
            'rows': 6
        })


class DonationForm(forms.ModelForm):
    """Donation form with validation"""
    
    class Meta:
        model = Donation
        fields = ['amount', 'donation_type', 'donor_name', 'donor_email', 'message', 'is_anonymous']
        
    amount = forms.DecimalField(
        validators=[MinValueValidator(1.00)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '25.00',
            'min': '1.00',
            'step': '0.01'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['donor_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Your Full Name'
        })
        self.fields['donor_email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
        self.fields['message'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Optional message with your donation...',
            'rows': 4
        })
        self.fields['donation_type'].widget.attrs.update({
            'class': 'form-control'
        })


class NewsletterForm(forms.ModelForm):
    """Newsletter subscription form"""
    
    class Meta:
        model = Newsletter
        fields = ['email', 'name']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Your name (optional)'
        })
