import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { ToastrService } from 'ngx-toastr';
import { MatDialog } from '@angular/material/dialog';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

@Component({
  selector: 'app-regulations',
  templateUrl: './regulations.component.html',
  styleUrls: ['./regulations.component.css']
})
export class RegulationsComponent implements OnInit {
  displayedColumns: string[] = [
    'id',
    'name',
    'value',
    'description',
    'created_at',
    'last_updated'
  ];

  dataSource = new MatTableDataSource<any>([]);
  isLoading = true;

  // For the Add/Edit form:
  regulationForm: FormGroup;
  isEditMode = false;
  editItemId: number | null = null;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild('regulationDialog') regulationDialog!: TemplateRef<any>;

  constructor(
    private http: HttpClient,
    private toastr: ToastrService,
    private dialog: MatDialog,
    private fb: FormBuilder
  ) {
    // Initialize form
    this.regulationForm = this.fb.group({
      name: ['', Validators.required],
      value: ['', Validators.required],
      description: ['']
    });
  }

  ngOnInit(): void {
    this.fetchRegulations();
  }

  fetchRegulations(): void {
    this.isLoading = true;

    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      this.toastr.error('No access token found. Please log in.', 'Error');
      this.isLoading = false;
      return;
    }

    const headers = new HttpHeaders({ Authorization: `Bearer ${accessToken}` });
    const endpoint = 'http://localhost:8000/api/regulationsregulations/';

    this.http.get<any[]>(endpoint, { headers }).subscribe({
      next: (data) => {
        this.dataSource.data = data;
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error fetching regulations:', err);
        this.toastr.error('Failed to fetch regulations.', 'Error');
        this.isLoading = false;
      }
    });
  }

  // Open the modal in "add" mode
  openAddRegulationModal(): void {
    this.isEditMode = false;
    this.editItemId = null;
    this.regulationForm.reset(); // clear old data if any
    this.dialog.open(this.regulationDialog, {
      width: '800px'
    });
  }

  // (Optional) If you want to do "edit" in the same dialog
  openEditRegulationModal(item: any): void {
    this.isEditMode = true;
    this.editItemId = item.id;
    this.regulationForm.patchValue({
      name: item.name,
      value: item.value,
      description: item.description
    });
    this.dialog.open(this.regulationDialog, {
      width: '800px'
    });
  }

  submitRegulation(): void {
    if (this.regulationForm.invalid) return;

    const accessToken = localStorage.getItem('access_token');
    const headers = new HttpHeaders({ Authorization: `Bearer ${accessToken}` });
    const endpoint = 'http://localhost:8000/api/regulationsregulations/';

    const payload = this.regulationForm.value;

    if (this.isEditMode && this.editItemId) {
      // Edit existing regulation
      const updateUrl = `${endpoint}${this.editItemId}/`;
      this.http.put(updateUrl, payload, { headers }).subscribe({
        next: () => {
          this.toastr.success('Regulation updated successfully', 'Success');
          this.dialog.closeAll();
          this.fetchRegulations();
        },
        error: (err) => {
          console.error('Error updating regulation:', err);
          this.toastr.error('Failed to update regulation', 'Error');
        }
      });
    } else {
      // Create new regulation
      this.http.post(endpoint, payload, { headers }).subscribe({
        next: () => {
          this.toastr.success('Regulation created successfully', 'Success');
          this.dialog.closeAll();
          this.fetchRegulations();
        },
        error: (err) => {
          console.error('Error creating regulation:', err);
          this.toastr.error('Failed to create regulation', 'Error');
        }
      });
    }
  }

  exportToCSV(): void {
    // your CSV logic
  }

  printTable(): void {
    // your Print logic
  }
}
