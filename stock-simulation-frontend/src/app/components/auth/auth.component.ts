import { Component } from '@angular/core';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-auth',
  templateUrl: './auth.component.html',
  styleUrls: ['./auth.component.css']
})
export class AuthComponent {
  user = { username: '', email: '', password: '', role: 'trader' };
  loginUser = { username: '', password: '' };
  selectedFile: File | null = null;

  constructor(private authService: AuthService) { }

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  onRegister() {
    const formData = new FormData();
    formData.append('username', this.user.username);
    formData.append('email', this.user.email);
    formData.append('password', this.user.password);
    formData.append('role', this.user.role);
    if (this.selectedFile) {
      formData.append('kyc_document', this.selectedFile);
    }

    this.authService.register(formData).subscribe(
      response => console.log('User registered successfully', response),
      error => console.error('Error registering user', error)
    );
  }

  onLogin() {
    this.authService.login(this.loginUser).subscribe(
      response => {
        console.log('User logged in successfully', response);
        localStorage.setItem('access_token', response.access);
        localStorage.setItem('refresh_token', response.refresh);
      },
      error => console.error('Error logging in', error)
    );
  }
}
