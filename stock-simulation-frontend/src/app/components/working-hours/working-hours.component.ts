// src/app/working-hours/working-hours.component.ts

import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { ToastrService } from 'ngx-toastr';
import { MatDialog } from '@angular/material/dialog';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService, WorkingHour } from '../../services/api.service';

@Component({
  selector: 'app-working-hours',
  templateUrl: './working-hours.component.html',
  styleUrls: ['./working-hours.component.css']
})
export class WorkingHoursComponent implements OnInit {
  displayedColumns: string[] = ['id', 'day_of_week', 'start_time', 'end_time'];
  dataSource = new MatTableDataSource<WorkingHour>([]);
  isLoading = true;

  // For Add/Edit form
  workingHourForm: FormGroup;
  isEditMode = false;
  editItemId: number | null = null;

  daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild('workingHourDialog') workingHourDialog!: TemplateRef<any>;

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    private dialog: MatDialog,
    private fb: FormBuilder
  ) {
    // Initialize the form
    this.workingHourForm = this.fb.group({
      day_of_week: ['', Validators.required],
      start_time: ['', Validators.required],
      end_time: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.fetchWorkingHours();
  }

  fetchWorkingHours(): void {
    this.isLoading = true;
    this.apiService.getWorkingHours().subscribe({
      next: (data) => {
        this.dataSource.data = data;
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error fetching working hours:', err);
        this.toastr.error('Failed to fetch working hours.', 'Error');
        this.isLoading = false;
      }
    });
  }

  openAddWorkingHourModal(): void {
    this.isEditMode = false;
    this.editItemId = null;
    this.workingHourForm.reset();
    this.dialog.open(this.workingHourDialog, { width: '800px' });
  }

  openEditWorkingHourModal(item: WorkingHour): void {
    this.isEditMode = true;
    this.editItemId = item.id || null;
    this.workingHourForm.patchValue({
      day_of_week: item.day_of_week,
      start_time: item.start_time,
      end_time: item.end_time
    });
    this.dialog.open(this.workingHourDialog, { width: '800px' });
  }

  submitWorkingHour(): void {
    if (this.workingHourForm.invalid) return;

    const payload: WorkingHour = this.workingHourForm.value;

    if (this.isEditMode && this.editItemId) {
      // Update existing working hour
      this.apiService.updateWorkingHour(this.editItemId, payload).subscribe({
        next: () => {
          this.toastr.success('Working hour updated successfully.', 'Success');
          this.dialog.closeAll();
          this.fetchWorkingHours();
        },
        error: (err) => {
          console.error('Error updating working hour:', err);
          this.toastr.error('Failed to update working hour.', 'Error');
        }
      });
    } else {
      // Create new working hour
      this.apiService.createWorkingHour(payload).subscribe({
        next: () => {
          this.toastr.success('Working hour created successfully.', 'Success');
          this.dialog.closeAll();
          this.fetchWorkingHours();
        },
        error: (err) => {
          console.error('Error creating working hour:', err);
          this.toastr.error('Failed to create working hour.', 'Error');
        }
      });
    }
  }

  deleteWorkingHour(id: number): void {
    if (confirm('Are you sure you want to delete this working hour entry?')) {
      this.apiService.deleteWorkingHour(id).subscribe({
        next: () => {
          this.toastr.success('Working hour deleted successfully.', 'Success');
          this.fetchWorkingHours();
        },
        error: (err) => {
          console.error('Error deleting working hour:', err);
          this.toastr.error('Failed to delete working hour.', 'Error');
        }
      });
    }
  }

  exportToCSV(): void {
    // Implement your CSV export logic here
  }

  printTable(): void {
    window.print();
  }
}
