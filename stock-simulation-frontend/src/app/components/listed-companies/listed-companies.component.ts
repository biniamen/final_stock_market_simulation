// src/app/components/listed-companies/listed-companies.component.ts

import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { ToastrService } from 'ngx-toastr';
import { HttpClient, HttpHeaders } from '@angular/common/http';

export interface ListedCompany {
  id: number;
  company_name: string;
  sector: string;
  last_updated: string;
}

@Component({
  selector: 'app-listed-companies',
  templateUrl: './listed-companies.component.html',
  styleUrls: ['./listed-companies.component.css']
})
export class ListedCompaniesComponent implements OnInit {
  displayedColumns: string[] = ['id', 'company_name', 'sector', 'last_updated', 'actions'];
  dataSource = new MatTableDataSource<ListedCompany>([]);
  isLoading = true;

  // Form for Add/Edit
  companyForm: FormGroup;
  isEditMode = false;
  editCompanyId: number | null = null;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild('companyDialog') companyDialog!: TemplateRef<any>;

  constructor(
   // private apiService: ApiService,
    private toastr: ToastrService,
    private dialog: MatDialog,
    private fb: FormBuilder,
    private http: HttpClient
  ) {
    // Initialize the form
    this.companyForm = this.fb.group({
      company_name: ['', Validators.required],
      sector: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.fetchListedCompanies();
  }

  // ---------------------------
  //        API FETCHES
  // ---------------------------
  fetchListedCompanies(): void {
    this.isLoading = true;
    this.http.get<ListedCompany[]>('http://localhost:8000/api/stocks/companies/').subscribe({
      next: (data) => {
        this.dataSource.data = data;
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error fetching listed companies:', err);
        this.toastr.error('Failed to fetch listed companies.', 'Error');
        this.isLoading = false;
      }
    });
  }

  // ---------------------------
  //       DIALOG OPEN
  // ---------------------------
  openAddCompanyModal(): void {
    this.isEditMode = false;
    this.editCompanyId = null;
    // Reset form
    this.companyForm.reset({
      company_name: '',
      sector: ''
    });
    this.dialog.open(this.companyDialog, { width: '600px' });
  }

  openEditCompanyModal(company: ListedCompany): void {
    this.isEditMode = true;
    this.editCompanyId = company.id;
    // Patch form with existing company data
    this.companyForm.patchValue({
      company_name: company.company_name,
      sector: company.sector
    });
    this.dialog.open(this.companyDialog, { width: '600px' });
  }

  // ---------------------------
  //      CREATE/UPDATE
  // ---------------------------
  submitCompany(): void {
    if (this.companyForm.invalid) return;

    const formValue = this.companyForm.value;

    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    if (this.isEditMode && this.editCompanyId) {
      // Update existing company
      this.http.put<ListedCompany>(`http://localhost:8000/api/stocks/companies/${this.editCompanyId}/`, formValue, { headers }).subscribe({
        next: (data) => {
          this.toastr.success('Company updated successfully.', 'Success');
          this.dialog.closeAll();
          this.fetchListedCompanies();
        },
        error: (err) => {
          console.error('Error updating company:', err);
          this.toastr.error('Failed to update company.', 'Error');
        }
      });
    } else {
      // Create new company
      this.http.post<ListedCompany>('http://localhost:8000/api/stocks/companies/', formValue, { headers }).subscribe({
        next: (data) => {
          this.toastr.success('Company added successfully.', 'Success');
          this.dialog.closeAll();
          this.fetchListedCompanies();
        },
        error: (err) => {
          console.error('Error adding company:', err);
          this.toastr.error('Failed to add company.', 'Error');
        }
      });
    }
  }

  // ---------------------------
  //        DELETE
  // ---------------------------
  deleteCompany(id: number): void {
    if (confirm('Are you sure you want to delete this company?')) {
      this.http.delete(`http://localhost:8000/api/stocks/companies/${id}/`).subscribe({
        next: () => {
          this.toastr.success('Company deleted successfully.', 'Success');
          this.fetchListedCompanies();
        },
        error: (err) => {
          console.error('Error deleting company:', err);
          this.toastr.error('Failed to delete company.', 'Error');
        }
      });
    }
  }

  // ---------------------------
  //     UTILITY ACTIONS
  // ---------------------------
  exportToCSV(): void {
    // Implement CSV export logic if needed
    // You can use libraries like ngx-csv or manually create a CSV string and trigger download
  }

  printTable(): void {
    window.print();
  }
}

// Service Interface (Assuming ApiService is similar to the one used in SuspensionsComponent)
export interface ApiService {
  getSuspensions(): any;
  getTraders(): any;
  getStocks(): any;
  createSuspension(data: any): any;
  updateSuspension(id: number, data: any): any;
  releaseSuspension(id: number): any;
  deleteSuspension(id: number): any;
}
