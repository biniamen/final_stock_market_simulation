import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DividendDetailedHoldingsComponent } from './dividend-detailed-holdings.component';

describe('DividendDetailedHoldingsComponent', () => {
  let component: DividendDetailedHoldingsComponent;
  let fixture: ComponentFixture<DividendDetailedHoldingsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DividendDetailedHoldingsComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DividendDetailedHoldingsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
