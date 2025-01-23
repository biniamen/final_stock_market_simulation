import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { ToastrService } from 'ngx-toastr';
import { MatDialog } from '@angular/material/dialog';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService, Suspension } from '../../services/api.service';

@Component({
  selector: 'app-suspensions',
  templateUrl: './suspensions.component.html',
  styleUrls: ['./suspensions.component.css']
})
export class SuspensionsComponent implements OnInit {
  displayedColumns: string[] = [
    'id',
    'trader',
    'stock',
    'suspension_type',
    'initiator',
    'reason',
    'is_active',
    'created_at',
    'released_at'
  ];
  dataSource = new MatTableDataSource<Suspension>([]);
  isLoading = true;

  // For Add/Edit form
  suspensionForm: FormGroup;
  isEditMode = false;
  editItemId: number | null = null;

  // For dropdowns
  traders: any[] = [];  // array of all traders (id, name, etc.)
  stocks: any[] = [];   // array of all stocks (id, name, etc.)

  // Example: “Specific Stock” or “All Stocks”
  suspensionTypes = ['Specific Stock', 'All Stocks'];

  // Example: “Listing Company” or “Regulatory Body”
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
      // Check = Suspended, Uncheck = Released
      is_active: [true]
    });
  }

  ngOnInit(): void {
    this.fetchSuspensions();
    this.fetchTraders();
    this.fetchStocks();
    this.handleSuspensionTypeChange();
  }

  // Fetch all suspensions
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

  // Fetch all traders for the dropdown
  fetchTraders(): void {
    this.apiService.getTraders().subscribe({
      next: (data) => {
        this.traders = data; // assume data is an array of {id, name} or similar
      },
      error: (err) => {
        console.error('Error fetching traders:', err);
        this.toastr.error('Failed to fetch traders.', 'Error');
      }
    });
  }

  // Fetch all stocks for the dropdown
  fetchStocks(): void {
    this.apiService.getStocks().subscribe({
      next: (data) => {
        this.stocks = data; // assume data is an array of {id, name} or similar
      },
      error: (err) => {
        console.error('Error fetching stocks:', err);
        this.toastr.error('Failed to fetch stocks.', 'Error');
      }
    });
  }

  // Open dialog for creating a new suspension
  openAddSuspensionModal(): void {
    this.isEditMode = false;
    this.editItemId = null;

    // Reset form to defaults
    this.suspensionForm.reset({
      trader: '',
      suspension_type: '',
      stock: '',
      initiator: '',
      reason: '',
      is_active: true
    });

    // Enable the trader selection in add mode
    this.suspensionForm.get('trader')?.enable();

    this.dialog.open(this.suspensionDialog, { width: '800px' });
  }

  // Open dialog for editing an existing suspension
  openEditSuspensionModal(item: Suspension): void {
    this.isEditMode = true;
    this.editItemId = item.id || null;

    // Patch form with existing data
    this.suspensionForm.patchValue({
      trader: item.trader,
      suspension_type: item.suspension_type,
      stock: item.stock || '',
      initiator: item.initiator,
      reason: item.reason,
      is_active: item.is_active // true => suspended, false => released
    });

    // Make trader read-only (disabled) in edit mode
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
        stockControl?.setValue(''); // reset the stock field
      }
      stockControl?.updateValueAndValidity();
    });
  }

  // Create or update a suspension
  submitSuspension(): void {
    // If form invalid, do nothing
    if (this.suspensionForm.invalid) return;

    // Collect payload
    // Note: If trader field is disabled (edit mode), .value will be empty;
    //       use getRawValue() to retrieve disabled control values.
    const formValue = this.suspensionForm.getRawValue();
    const payload: Suspension = {
      ...formValue
      // If you need to map fields, do it here
    };

    // Distinguish between create vs. update
    if (this.isEditMode && this.editItemId) {
      // Update existing suspension
      this.apiService.updateSuspension(this.editItemId, payload).subscribe({
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
      // Create new suspension
      this.apiService.createSuspension(payload).subscribe({
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

  // Delete a suspension
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

  // Release a suspension (shortcut method, if needed)
  releaseSuspension(id: number): void {
    if (confirm('Are you sure you want to release this suspension?')) {
      this.apiService.releaseSuspension(id).subscribe({
        next: () => {
          this.toastr.success('Suspension released successfully.', 'Success');
          this.fetchSuspensions();
        },
        error: (err) => {
          console.error('Error releasing suspension:', err);
          this.toastr.error('Failed to release suspension.', 'Error');
        }
      });
    }
  }

  // Export table to CSV
  exportToCSV(): void {
    // Implement your CSV export logic here
  }

  // Print the table
  printTable(): void {
    window.print();
  }
}
