import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-forgot-password',
  templateUrl: './forgot-password.component.html',
  styleUrls: ['./forgot-password.component.css']
})
export class ForgotPasswordComponent {
  forgotPasswordForm: FormGroup;
  isLoading = false;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private toastr: ToastrService
  ) {
    this.forgotPasswordForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    });
  }

  onSubmit(): void {
    if (this.forgotPasswordForm.invalid) return;

    this.isLoading = true;
    const email = this.forgotPasswordForm.value.email;

    this.http.post<any>('http://localhost:8000/api/users/forgot-password/', { email }).subscribe({
      next: (res) => {
        this.toastr.success(res.detail || 'If email is registered, a reset link was sent.', 'Success');
        this.isLoading = false;
      },
      error: (err) => {
        console.error(err);
        const message = err.error?.detail || 'Failed to send reset link.';
        this.toastr.error(message, 'Error');
        this.isLoading = false;
      }
    });
  }
}
