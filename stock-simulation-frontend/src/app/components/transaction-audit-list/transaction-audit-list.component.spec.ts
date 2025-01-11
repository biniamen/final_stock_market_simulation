import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TransactionAuditListComponent } from './transaction-audit-list.component';

describe('TransactionAuditListComponent', () => {
  let component: TransactionAuditListComponent;
  let fixture: ComponentFixture<TransactionAuditListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TransactionAuditListComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TransactionAuditListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
