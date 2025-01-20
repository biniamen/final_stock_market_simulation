import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddDividendDialogComponent } from './add-dividend-dialog.component';

describe('AddDividendDialogComponent', () => {
  let component: AddDividendDialogComponent;
  let fixture: ComponentFixture<AddDividendDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AddDividendDialogComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AddDividendDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
