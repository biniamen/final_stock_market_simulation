import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UserTradedComponent } from './user-traded.component';

describe('UserTradedComponent', () => {
  let component: UserTradedComponent;
  let fixture: ComponentFixture<UserTradedComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ UserTradedComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(UserTradedComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
