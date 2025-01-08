import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  username: string | null = '';
  kycStatus: string | null = '';

  constructor(private router: Router) {}

  ngOnInit(): void {
    // Fetch username and KYC status from localStorage (or API if available)
    this.username = localStorage.getItem('username');
    this.kycStatus = localStorage.getItem('kyc_status');
  }

  onLogout() {
    // Clear the localStorage and redirect to login page
    localStorage.clear();
    this.router.navigate(['/login']);
  }
}
