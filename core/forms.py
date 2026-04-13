# core/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Post, Comment, Profile, Message


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-input', 'placeholder': 'Email address',
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-input'})
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters long.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-input',
        'placeholder': 'Username',
        'autocomplete': 'username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': 'Password',
        'autocomplete': 'current-password',
    }))


class PostForm(forms.ModelForm):
    """
    Post form supports both image+caption and text-only posts.
    Image is optional — if omitted, a text-only post is created.
    """
    class Meta:
        model = Post
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': "What's on your mind?",
                'rows': 4,
            }),
            'image': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'image-upload',
                'accept': 'image/*',
            }),
        }

    def clean(self):
        cleaned = super().clean()
        image = cleaned.get('image')
        caption = cleaned.get('caption', '').strip()
        if not image and not caption:
            raise forms.ValidationError("Please add an image or write some text.")
        return cleaned


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Add a comment...',
                'autocomplete': 'off',
            }),
        }

    def clean_content(self):
        content = self.cleaned_data['content'].strip()
        if len(content) < 2:
            raise forms.ValidationError('Comment must be at least 2 characters long.')
        return content


class ProfileEditForm(forms.ModelForm):
    """
    Form for editing bio and avatar.
    Avatar widget is hidden in this form because the template renders
    a plain <input type="file" name="avatar"> directly, triggered by the camera button.
    The form still validates and saves the avatar field from request.FILES.
    """
    class Meta:
        model = Profile
        fields = ['bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Tell your story...',
                'rows': 3,
            }),
            # Avatar is rendered manually in template — hide the Django-generated widget
            'avatar': forms.FileInput(attrs={'style': 'display:none;', 'id': 'django-avatar-input'}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'msg-input',
                'placeholder': 'Message...',
                'autocomplete': 'off',
            }),
        }

    def clean_content(self):
        content = self.cleaned_data['content'].strip()
        if len(content) < 1:
            raise forms.ValidationError('Message cannot be empty.')
        return content


class AdminUserForm(forms.ModelForm):
    password = forms.CharField(required=False, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'is_staff', 'is_active', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class AdminPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['author', 'caption']


class AdminCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['post', 'author', 'content']
