import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { ToastrService } from 'ngx-toastr';
import { MatDialog } from '@angular/material/dialog';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { saveAs } from 'file-saver';

interface Regulation {
  id: number;
  name: string;
  value: number | string;
  description: string;
  created_at: string;
  last_updated: string;
}

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
    'last_updated',
    'actions'
  ];

  dataSource = new MatTableDataSource<Regulation>([]);
  isLoading = true;

  // Predefined regulation names
  regulationNames: string[] = [
    'Daily Trade Limit',
    'Daily Trading Amount',
   
  ];

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

    this.http.get<Regulation[]>(endpoint, { headers }).subscribe({
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
      width: '600px'
    });
  }

  // Open the modal in "edit" mode
  openEditRegulationModal(item: Regulation): void {
    this.isEditMode = true;
    this.editItemId = item.id;
    this.regulationForm.patchValue({
      name: item.name,
      value: item.value,
      description: item.description
    });
    this.dialog.open(this.regulationDialog, {
      width: '600px'
    });
  }

  submitRegulation(): void {
    if (this.regulationForm.invalid) return;
  
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      this.toastr.error('No access token found. Please log in.', 'Error');
      return;
    }
  
    const headers = new HttpHeaders({ Authorization: `Bearer ${accessToken}` });
    const endpoint = 'http://localhost:8000/api/regulationsregulations/';
  
    const payload = this.regulationForm.value;
  
    if (this.isEditMode && this.editItemId) {
      // Edit existing regulation
      const updateUrl = `${endpoint}${this.editItemId}/`;
      this.http.put<Regulation>(updateUrl, payload, { headers }).subscribe({
        next: (updatedRegulation) => {
          this.toastr.success('Regulation updated successfully', 'Success');
          this.dialog.closeAll();
          this.updateRegulationInDataSource(updatedRegulation);
        },
        error: (err) => {
          console.error('Error updating regulation:', err);
          if (err.error && typeof err.error === 'object') {
            Object.keys(err.error).forEach((key) => {
              const messages = err.error[key];
              messages.forEach((message: string) => {
                this.toastr.error(`${key}: ${message}`, 'Error');
              });
            });
          } else {
            this.toastr.error('Failed to update regulation', 'Error');
          }
        }
      });
    } else {
      // Create new regulation
      this.http.post<Regulation>(endpoint, payload, { headers }).subscribe({
        next: (newRegulation) => {
          this.toastr.success('Regulation created successfully', 'Success');
          this.dialog.closeAll();
          this.addRegulationToDataSource(newRegulation);
        },
        error: (err) => {
          console.error('Error creating regulation:', err);
          if (err.error && typeof err.error === 'object') {
            Object.keys(err.error).forEach((key) => {
              const messages = err.error[key];
              messages.forEach((message: string) => {
                this.toastr.error(`${key}: ${message}`, 'Error');
              });
            });
          } else {
            this.toastr.error('Failed to create regulation', 'Error');
          }
        }
      });
    }
  }
  
  // Helper methods to update the dataSource without refetching
  updateRegulationInDataSource(updatedRegulation: Regulation): void {
    const index = this.dataSource.data.findIndex(r => r.id === updatedRegulation.id);
    if (index !== -1) {
      this.dataSource.data[index] = updatedRegulation;
      this.dataSource._updateChangeSubscription(); // Refresh the table
    }
  }

  addRegulationToDataSource(newRegulation: Regulation): void {
    this.dataSource.data = [newRegulation, ...this.dataSource.data];
  }

  // Search functionality
  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();

    // Reset to the first page if filtering
    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  // Export to CSV
  exportToCSV(): void {
    if (this.dataSource.data.length === 0) {
      this.toastr.info('No data available to export.', 'Info');
      return;
    }

    const headers = this.displayedColumns.filter(col => col !== 'actions');
    const csvRows = [];

    // Add header row
    csvRows.push(headers.join(','));

    // Add data rows
    this.dataSource.filteredData.forEach(regulation => {
      const row = headers.map(header => {
        let cell = (regulation as any)[header];
        if (typeof cell === 'string') {
          // Escape double quotes
          cell = cell.replace(/"/g, '""');
          // Wrap in double quotes if it contains a comma
          if (cell.includes(',')) {
            cell = `"${cell}"`;
          }
        }
        return cell;
      });
      csvRows.push(row.join(','));
    });

    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const filename = 'regulations_export.csv';
    saveAs(blob, filename);
    this.toastr.success('Regulations exported successfully.', 'Success');
  }

  // Print functionality
  printTable(): void {
    const printContents = document.getElementById('print-section')?.innerHTML;
    if (!printContents) {
      this.toastr.error('Nothing to print.', 'Error');
      return;
    }

    const originalContents = document.body.innerHTML;
    document.body.innerHTML = printContents;

    window.print();

    // Restore original contents after printing
    document.body.innerHTML = originalContents;
    window.location.reload(); // Reload to re-initialize Angular bindings
  }

  // Delete Regulation (Optional Enhancement)
  deleteRegulation(regulation: Regulation): void {
    if (!confirm(`Are you sure you want to delete regulation "${regulation.name}"?`)) {
      return;
    }

    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      this.toastr.error('No access token found. Please log in.', 'Error');
      return;
    }

    const headers = new HttpHeaders({ Authorization: `Bearer ${accessToken}` });
    const deleteUrl = `http://localhost:8000/api/regulationsregulations/${regulation.id}/`;

    this.http.delete(deleteUrl, { headers }).subscribe({
      next: () => {
        this.toastr.success('Regulation deleted successfully', 'Success');
        this.removeRegulationFromDataSource(regulation.id);
      },
      error: (err) => {
        console.error('Error deleting regulation:', err);
        this.toastr.error('Failed to delete regulation', 'Error');
      }
    });
  }

  removeRegulationFromDataSource(id: number): void {
    this.dataSource.data = this.dataSource.data.filter(r => r.id !== id);
  }
}
