// src/app/components/user-list/user-list.component.ts

import { Component, OnInit, ViewChild } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { UserService } from '../../services/user.service';
import { ToastrService } from 'ngx-toastr';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import { MatDialog } from '@angular/material/dialog';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.ts.component.html', // Corrected path
  styleUrls: ['./user-list.component.ts.component.css']   // Corrected path
})
export class UserListComponent implements OnInit {
  displayedColumns: string[] = [
    'id',
    'username',
    'email',
    'role',
    'kyc_verified',
    'otp_verified',
    'is_approved',
    'date_registered',
    'last_login',
    'actions',
    'view_kyc'
  ];
  dataSource: MatTableDataSource<any> = new MatTableDataSource();
  isLoading: boolean = true;
  currentUserRole: string | null = null;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private userService: UserService,
    private toastr: ToastrService,
    public dialog: MatDialog
  ) { }

  ngOnInit(): void {
    const role = localStorage.getItem('role');
    this.currentUserRole = role ? role.toLowerCase() : null;
    console.log('Current User Role:', this.currentUserRole); // Debugging
    this.fetchUsers();
  }

  fetchUsers(): void {
    this.isLoading = true;
    this.userService.getUsers().subscribe(
      (data) => {
        this.dataSource.data = data;
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.isLoading = false;
        console.log(data);
      },
      (error) => {
        console.error('Error fetching users', error);
        const errorMessage = error.error?.detail || 'Failed to load users';
        this.toastr.error(errorMessage, 'Error');
        this.isLoading = false;
      }
    );
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();

    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  exportToCSV(): void {
    const dataToExport = this.dataSource.data.map(user => ({
      ID: user.id,
      Username: user.username,
      Email: user.email,
      Role: user.role,
      'KYC Verified': user.kyc_verified ? 'Yes' : 'No',
      'OTP Verified': user.otp_verified ? 'Yes' : 'No',
      'Is Approved': user.is_approved ? 'Yes' : 'No',
      'Date Registered': new Date(user.date_registered).toLocaleString(),
      'Last Login': user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'
    }));
  
    const worksheet: XLSX.WorkSheet = XLSX.utils.json_to_sheet(dataToExport);
    const workbook: XLSX.WorkBook = { Sheets: { 'Users': worksheet }, SheetNames: ['Users'] };
    const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    const blob: Blob = new Blob([excelBuffer], { type: 'application/octet-stream' });
    saveAs(blob, 'User_List.xlsx');
  }
  
  printTable(): void {
    const printContents = document.getElementById('userTable')?.innerHTML;
    const originalContents = document.body.innerHTML;

    if (printContents) {
      document.body.innerHTML = printContents;
      window.print();
      document.body.innerHTML = originalContents;
      window.location.reload();
    }
  }

  approveKyc(user: any): void {
    if (!user.otp_verified) {
      this.toastr.error('Cannot approve KYC. OTP not verified.', 'Error');
      return;
    }
    this.userService.approveKyc(user.id).subscribe(
      (response) => {
        const successMessage = response.message || 'KYC approved successfully.';
        this.toastr.success(successMessage, 'Success');
        this.fetchUsers(); // Refresh the table
      },
      (error) => {
        console.error('Error approving KYC', error);
        const errorMessage = error.error?.detail || 'Failed to approve KYC.';
        this.toastr.error(errorMessage, 'Error');
      }
    );
  }

  rejectKyc(user: any): void {
    this.userService.rejectKyc(user.id).subscribe(
      (response) => {
        const successMessage = response.message || 'KYC rejected successfully.';
        this.toastr.success(successMessage, 'Success');
        this.fetchUsers(); // Refresh the table
      },
      (error) => {
        console.error('Error rejecting KYC', error);
        const errorMessage = error.error?.detail || 'Failed to reject KYC.';
        this.toastr.error(errorMessage, 'Error');
      }
    );
  }

  deactivateUser(user: any): void {
    const confirmDeactivate = confirm(`Are you sure you want to deactivate user ${user.username}?`);
    if (confirmDeactivate) {
      this.userService.deactivateUser(user.id).subscribe(
        (response) => {
          const successMessage = response.message || 'User deactivated successfully.';
          this.toastr.success(successMessage, 'Success');
          this.fetchUsers(); // Refresh the table
        },
        (error) => {
          console.error('Error deactivating user', error);
          const errorMessage = error.error?.detail || 'Failed to deactivate user.';
          this.toastr.error(errorMessage, 'Error');
        }
      );
    }
  }

  viewKyc(user: any): void {
    if (user.kyc_document) {
      const documentUrl = `${environment.baseUrl}${user.kyc_document}`;
      try {
        new URL(documentUrl); // Validate URL
        window.open(documentUrl, '_blank');
      } catch (error) {
        console.error('Invalid KYC document URL:', documentUrl);
        this.toastr.error('Invalid KYC document URL.', 'Error');
      }
    } else {
      this.toastr.error('No KYC document available.', 'Error');
    }
  }
  
  // Tooltip helper methods
  getApproveTooltip(element: any): string {
    if (!element.otp_verified) {
      return 'OTP needs to be verified to approve the user';
    }
    if (element.is_approved) {
      return 'User is already approved';
    }
    if (element.kyc_verified) {
      return 'KYC is already verified';
    }
    return ''; // No tooltip if the button is enabled
  }

  getRejectTooltip(element: any): string {
    if (!element.is_approved && !element.kyc_verified) {
      return 'Cannot reject without approval or KYC verification';
    }
    return ''; // No tooltip if the button is enabled
  }

  getDeactivateTooltip(element: any): string {
    if (!element.is_approved) {
      return 'User is already deactivated';
    }
    return ''; // No tooltip if the button is enabled
  }
}
