// suspicious-activities.component.ts

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

  /**
   * Suspend the trader and mark the activity as reviewed.
   */
  suspendTrader(activity: ISuspiciousActivity): void {
    if (!activity.trade || !activity.trade.user || !activity.trade.stock) {
      this.toastr.error('Invalid activity data. Cannot suspend trader.', 'Error');
      return;
    }

    if (
      !confirm(
        `Are you sure you want to suspend trader '${activity.trade.user.username}' 
         for stock '${activity.trade.stock.ticker_symbol}'?`
      )
    ) {
      return;
    }

    const payload = {
      trader: activity.trade.user.id,
      stock: activity.trade.stock.id,
      suspension_type: 'Specific Stock',
      initiator: 'Regulatory Body',
      reason: activity.reason
    };

    // 1) Suspend the trader
    this.suspiciousActivityService.suspendTrader(payload).subscribe({
      next: () => {
        // 2) Mark suspicious activity as reviewed
        const updatedActivity: ISuspiciousActivity = { ...activity, reviewed: true };
        this.suspiciousActivityService.updateActivity(activity.id, updatedActivity).subscribe({
          next: () => {
            this.toastr.success('Trader suspended & activity marked as reviewed.', 'Success');
            // Refresh the local data
            activity.reviewed = true;
            this.dataSource.data = [...this.dataSource.data];
          },
          error: (err: any) => {
            console.error('Error updating suspicious activity:', err);
            this.toastr.error('Failed to update suspicious activity record.', 'Error');
          }
        });
      },
      error: (err) => {
        this.toastr.error('Failed to suspend trader', 'Error');
        console.error(err);
      },
    });
  }

  /**
   * Ignore the suspicious activity by deleting it.
   * @param activity The suspicious activity to ignore.
   */
  ignoreActivity(activity: ISuspiciousActivity): void {
    if (!confirm(`Are you sure you want to ignore and delete this suspicious activity (ID: ${activity.id})?`)) {
      return;
    }

    this.suspiciousActivityService.deleteActivity(activity.id).subscribe({
      next: () => {
        this.toastr.success('Suspicious activity has been ignored and deleted.', 'Success');
        // Remove the activity from the dataSource
        this.dataSource.data = this.dataSource.data.filter(a => a.id !== activity.id);
      },
      error: (err) => {
        this.toastr.error('Failed to ignore and delete the suspicious activity.', 'Error');
        console.error(err);
      },
    });
  }
}
