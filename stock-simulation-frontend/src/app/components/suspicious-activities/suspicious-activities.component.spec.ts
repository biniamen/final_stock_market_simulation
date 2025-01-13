import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SuspiciousActivitiesComponent } from './suspicious-activities.component';

describe('SuspiciousActivitiesComponent', () => {
  let component: SuspiciousActivitiesComponent;
  let fixture: ComponentFixture<SuspiciousActivitiesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SuspiciousActivitiesComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SuspiciousActivitiesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
