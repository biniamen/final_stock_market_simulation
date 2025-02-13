// src/app/components/suspensions/suspensions.component.ts

import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { ToastrService } from 'ngx-toastr';

import { ApiService, Suspension } from '../../services/api.service';

@Component({
  selector: 'app-suspensions',
  templateUrl: './suspensions.component.html',
  styleUrls: ['./suspensions.component.css']
})
export class SuspensionsComponent implements OnInit {
  displayedColumns: string[] = [
    'id',
    'trader_username',            // Updated column
    'stock_ticker_symbol',        // Updated column
    'suspension_type',
    'initiator',
    'reason',
    'is_active',
    'created_at',
    'released_at',
    'actions'                      // Added actions column for edit/delete
  ];
  dataSource = new MatTableDataSource<Suspension>([]);
  isLoading = true;

  // For Add/Edit form
  suspensionForm: FormGroup;
  isEditMode = false;
  editItemId: number | null = null;

  // For dropdowns
  traders: any[] = [];  // array of all traders (id, username, etc.)
  stocks: any[] = [];   // array of all stocks (id, ticker_symbol, etc.)
  suspensionTypes = ['Specific Stock', 'All Stocks'];
  initiators = ['Listing Company', 'Regulatory Body'];

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild('suspensionDialog') suspensionDialog!: TemplateRef<any>;

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    private dialog: MatDialog,
    private fb: FormBuilder
  ) {
    // Initialize the form
    this.suspensionForm = this.fb.group({
      trader: ['', Validators.required],
      suspension_type: ['', Validators.required],
      stock: [''],
      initiator: ['', Validators.required],
      reason: ['', Validators.required],
      // true => Suspended, false => Released
      is_active: [true]
    });
  }

  ngOnInit(): void {
    this.fetchSuspensions();
    this.fetchTraders();
    this.fetchStocks();
    this.handleSuspensionTypeChange();
  }

  // ---------------------------
  //        API FETCHES
  // ---------------------------
  fetchSuspensions(): void {
    this.isLoading = true;
    this.apiService.getSuspensions().subscribe({
      next: (data) => {
        this.dataSource.data = data;
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error fetching suspensions:', err);
        this.toastr.error('Failed to fetch suspensions.', 'Error');
        this.isLoading = false;
      }
    });
  }

  fetchTraders(): void {
    this.apiService.getTraders().subscribe({
      next: (data) => {
        this.traders = data;
      },
      error: (err) => {
        console.error('Error fetching traders:', err);
        this.toastr.error('Failed to fetch traders.', 'Error');
      }
    });
  }

  fetchStocks(): void {
    this.apiService.getStocks().subscribe({
      next: (data) => {
        this.stocks = data;
      },
      error: (err) => {
        console.error('Error fetching stocks:', err);
        this.toastr.error('Failed to fetch stocks.', 'Error');
      }
    });
  }

  // ---------------------------
  //       DIALOG OPEN
  // ---------------------------
  openAddSuspensionModal(): void {
    this.isEditMode = false;
    this.editItemId = null;
    // Reset form
    this.suspensionForm.reset({
      trader: '',
      suspension_type: '',
      stock: '',
      initiator: '',
      reason: '',
      is_active: true
    });
    // Enable trader selection
    this.suspensionForm.get('trader')?.enable();

    this.dialog.open(this.suspensionDialog, { width: '800px' });
  }

  openEditSuspensionModal(item: Suspension): void {
    this.isEditMode = true;
    this.editItemId = item.id || null;

    // Patch form
    this.suspensionForm.patchValue({
      trader: item.trader,
      suspension_type: item.suspension_type,
      stock: item.stock || '',
      initiator: item.initiator,
      reason: item.reason,
      is_active: item.is_active
    });

    // Make trader read-only
    this.suspensionForm.get('trader')?.disable();

    this.dialog.open(this.suspensionDialog, { width: '800px' });
  }

  // Conditionally require the "stock" field if "Specific Stock" is selected
  handleSuspensionTypeChange(): void {
    this.suspensionForm.get('suspension_type')?.valueChanges.subscribe(value => {
      const stockControl = this.suspensionForm.get('stock');
      if (value === 'Specific Stock') {
        stockControl?.setValidators([Validators.required]);
      } else {
        stockControl?.clearValidators();
        stockControl?.setValue('');
      }
      stockControl?.updateValueAndValidity();
    });
  }

  // ---------------------------
  //      CREATE/UPDATE
  // ---------------------------
  submitSuspension(): void {
    if (this.suspensionForm.invalid) return;

    // If trader is disabled in edit mode, we must use getRawValue
    const formValue = this.suspensionForm.getRawValue();

    if (this.isEditMode && this.editItemId) {
      // Update
      this.apiService.updateSuspension(this.editItemId, formValue).subscribe({
        next: () => {
          this.toastr.success('Suspension updated successfully.', 'Success');
          this.dialog.closeAll();
          this.fetchSuspensions();
        },
        error: (err) => {
          console.error('Error updating suspension:', err);
          this.toastr.error('Failed to update suspension.', 'Error');
        }
      });
    } else {
      // Create
      this.apiService.createSuspension(formValue).subscribe({
        next: () => {
          this.toastr.success('Suspension created successfully.', 'Success');
          this.dialog.closeAll();
          this.fetchSuspensions();
        },
        error: (err) => {
          console.error('Error creating suspension:', err);
          this.toastr.error('Failed to create suspension.', 'Error');
        }
      });
    }
  }

  // ---------------------------
  //      RELEASE SUSPENSION
  // ---------------------------
  releaseCurrentSuspension(): void {
    if (!this.editItemId) return;

    if (!confirm('Are you sure you want to release this trader from suspension?')) {
      return;
    }

    this.apiService.releaseSuspension(this.editItemId).subscribe({
      next: () => {
        this.toastr.success('Suspension released successfully.', 'Success');
        this.dialog.closeAll();
        this.fetchSuspensions();
      },
      error: (err) => {
        console.error('Error releasing suspension:', err);
        this.toastr.error('Failed to release suspension.', 'Error');
      }
    });
  }

  // ---------------------------
  //        DELETE
  // ---------------------------
  deleteSuspension(id: number): void {
    if (confirm('Are you sure you want to delete this suspension?')) {
      this.apiService.deleteSuspension(id).subscribe({
        next: () => {
          this.toastr.success('Suspension deleted successfully.', 'Success');
          this.fetchSuspensions();
        },
        error: (err) => {
          console.error('Error deleting suspension:', err);
          this.toastr.error('Failed to delete suspension.', 'Error');
        }
      });
    }
  }

  // ---------------------------
  //     UTILITY ACTIONS
  // ---------------------------
  exportToCSV(): void {
    // Implement CSV export logic
    // You can use libraries like ngx-csv or manually create a CSV string and trigger download
  }

  printTable(): void {
    window.print();
  }
}
