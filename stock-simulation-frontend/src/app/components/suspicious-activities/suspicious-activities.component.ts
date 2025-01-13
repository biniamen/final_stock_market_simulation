import { Component, OnInit, ViewChild } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { ToastrService } from 'ngx-toastr';
import { SuspiciousActivityService, ISuspiciousActivity } from '../../services/suspicious-activity.service';

@Component({
  selector: 'app-suspicious-activities',
  templateUrl: './suspicious-activities.component.html',
  styleUrls: ['./suspicious-activities.component.css'],
})
export class SuspiciousActivitiesComponent implements OnInit {
  displayedColumns: string[] = ['tradeInfo', 'reason', 'flagged_at', 'reviewed', 'actions'];
  dataSource = new MatTableDataSource<ISuspiciousActivity>();
  isLoading = true;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private suspiciousActivityService: SuspiciousActivityService,
    private toastr: ToastrService
  ) {}

  ngOnInit(): void {
    this.fetchActivities();
  }

  fetchActivities(): void {
    this.isLoading = true;
    this.suspiciousActivityService.getAllActivities().subscribe({
      next: (data) => {
        this.dataSource.data = data;
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.isLoading = false;
      },
      error: (err) => {
        this.toastr.error('Failed to load suspicious activities', 'Error');
        console.error(err);
        this.isLoading = false;
      },
    });
  }

  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();

    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  suspendTrader(activity: ISuspiciousActivity): void {
    if (!activity.trade || !activity.trade.user || !activity.trade.stock) {
      this.toastr.error('Invalid activity data. Cannot suspend trader.', 'Error');
      return;
    }
  
    if (
      !confirm(
        `Are you sure you want to suspend trader '${activity.trade.user.username}' for stock '${activity.trade.stock.ticker_symbol}'?`
      )
    ) {
      return;
    }
  
    const payload = {
      trader: activity.trade.user.id,
      stock: activity.trade.stock.id,
      suspension_type: 'Specific Stock',
      initiator: 'Regulatory Body',
      reason: activity.reason,
    };
  
    this.suspiciousActivityService.suspendTrader(payload).subscribe({
      next: () => {
        this.toastr.success('Trader suspended successfully', 'Success');
        activity.reviewed = true; // Set reviewed to true
        this.dataSource.data = [...this.dataSource.data]; // Refresh the table to reflect changes
      },
      error: (err) => {
        this.toastr.error('Failed to suspend trader', 'Error');
        console.error(err);
      },
    });
  }
  
}
