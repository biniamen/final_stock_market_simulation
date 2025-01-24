import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-reset-password',
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.css']
})
export class ResetPasswordComponent implements OnInit {
  resetPasswordForm: FormGroup;
  isLoading = false;
  token!: string;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private http: HttpClient,
    private toastr: ToastrService
  ) {
    this.resetPasswordForm = this.fb.group({
      new_password: ['', [Validators.required, Validators.minLength(8)]]
    });
  }

  ngOnInit(): void {
    // Extract token from URL query parameter
    this.route.queryParams.subscribe(params => {
      this.token = params['token'] || '';
      if (!this.token) {
        this.toastr.error('Invalid or missing token.', 'Error');
        this.router.navigate(['/login']); // or wherever you want
      }
    });
  }

  onSubmit(): void {
    if (this.resetPasswordForm.invalid) return;
    this.isLoading = true;

    const new_password = this.resetPasswordForm.value.new_password;
    const body = { token: this.token, new_password };

    this.http.post<any>('http://localhost:8000/api/users/reset-password/', body).subscribe({
      next: (res) => {
        this.toastr.success(res.detail || 'Password reset successfully.', 'Success');
        this.isLoading = false;
        this.router.navigate(['/login']); // or wherever you want after reset
      },
      error: (err) => {
        console.error(err);
        const message = err.error?.detail || 'Failed to reset password.';
        this.toastr.error(message, 'Error');
        this.isLoading = false;
      }
    });
  }
}
