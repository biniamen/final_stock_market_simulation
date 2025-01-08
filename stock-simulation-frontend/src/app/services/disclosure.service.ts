import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DisclosureService {
  private apiUrl = 'http://127.0.0.1:8000/api/stocks/disclosures/';
  private companyDisclosuresUrl = 'http://127.0.0.1:8000/api/stocks/company/';

  constructor(private http: HttpClient) {}

  // Helper to create headers with the access token
  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('Authentication token is missing. Please log in.');
    }
    return new HttpHeaders({
      Authorization: `Bearer ${token}` // Use Bearer token format
    });
  }

  // Fetch disclosures for a specific company
  getCompanyDisclosures(companyId: number): Observable<any[]> {
    const headers = this.getHeaders();
    return this.http.get<any[]>(`${this.companyDisclosuresUrl}${companyId}/disclosures/`, { headers: headers });
  }

  // Upload disclosure
  uploadDisclosure(formData: FormData): Observable<any> {
    const headers = this.getHeaders();
    return this.http.post(this.apiUrl, formData, { headers: headers });
  }
}
