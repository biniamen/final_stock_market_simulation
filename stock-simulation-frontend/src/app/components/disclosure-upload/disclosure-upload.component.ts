import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { DisclosureService } from 'src/app/services/disclosure.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-disclosure-upload',
  templateUrl: './disclosure-upload.component.html',
  styleUrls: ['./disclosure-upload.component.css']
})
export class DisclosureUploadComponent implements OnInit {
  disclosureForm!: FormGroup;
  selectedFile: File | null = null;
  dataSource = new MatTableDataSource<any>();
  displayedColumns: string[] = ['id', 'type', 'year', 'description', 'file'];
  disclosureTypes = ['Financial Statement', 'Annual Report', 'Material Event', 'Quarterly Report'];
  isLoading = true;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  // Reference the modal template using @ViewChild
  @ViewChild('modal', { static: true }) modal!: TemplateRef<any>;

  constructor(
    private fb: FormBuilder,
    private dialog: MatDialog,
    private disclosureService: DisclosureService,
    private toastr: ToastrService
  ) {}

  ngOnInit(): void {
    const companyId = localStorage.getItem('company_id');
    this.disclosureForm = this.fb.group({
      company: [companyId, Validators.required],
      type: [null, Validators.required],
      year: [null, [Validators.required, Validators.min(1900)]],
      description: [null]
    });

    if (companyId) {
      this.loadCompanyDisclosures(+companyId);
    }
  }

  loadCompanyDisclosures(companyId: number): void {
    this.isLoading = true;
    this.disclosureService.getCompanyDisclosures(companyId).subscribe({
      next: (data) => {
        this.dataSource.data = data;
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.isLoading = false;
      },
      error: (err) => {
        const errorMessage = err.error.detail || 'Failed to load disclosures.';
        this.toastr.error(errorMessage, 'Error');
        this.isLoading = false;
      }
    });
  }

  openModal(): void {
    const dialogRef = this.dialog.open(this.modal, {
      width: '600px',
      disableClose: true
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        const companyId = localStorage.getItem('company_id');
        if (companyId) {
          this.loadCompanyDisclosures(+companyId);
        }
      }
    });
  }

  closeModal(): void {
    this.dialog.closeAll();
  }

  onFileSelected(event: any): void {
    this.selectedFile = event.target.files[0] || null;
  }

  onSubmit(): void {
    if (!this.disclosureForm.valid || !this.selectedFile) {
      this.toastr.error('Please fill in all required fields.', 'Validation Error');
      return;
    }

    const formData = new FormData();
    formData.append('company', this.disclosureForm.value.company);
    formData.append('type', this.disclosureForm.value.type);
    formData.append('year', this.disclosureForm.value.year);
    formData.append('description', this.disclosureForm.value.description || '');
    formData.append('file', this.selectedFile);

    this.disclosureService.uploadDisclosure(formData).subscribe({
      next: (res) => {
        this.toastr.success('Disclosure uploaded successfully!', 'Success');
        this.closeModal();
        const companyId = this.disclosureForm.value.company;
        this.loadCompanyDisclosures(companyId);
      },
      error: (err) => {
        const errorMessage = err.error.detail || 'Failed to upload disclosure.';
        this.toastr.error(errorMessage, 'Error');
      }
    });
  }

  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();

    // Reset pagination to the first page when a filter is applied
    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }
}
