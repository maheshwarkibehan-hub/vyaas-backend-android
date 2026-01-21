"""
WhatsApp Web Automation Debug Script
This script shows where the automation will click on your screen.
Run this BEFORE testing the actual WhatsApp automation to verify positions.
"""

import pyautogui
import time
import webbrowser

def draw_marker(x, y, label):
    """Move mouse to position and display info"""
    print(f"\n🎯 {label}")
    print(f"   Position: ({x}, {y})")
    pyautogui.moveTo(x, y, duration=0.5)
    time.sleep(1.5)  # Hold position so user can see

def main():
    print("=" * 50)
    print("WhatsApp Web Automation Debug Script")
    print("=" * 50)
    
    # Get screen size
    screen_width, screen_height = pyautogui.size()
    print(f"\n📺 Your Screen Resolution: {screen_width} x {screen_height}")
    
    # Open WhatsApp Web
    print("\n🌐 Opening WhatsApp Web...")
    webbrowser.open("https://web.whatsapp.com/")
    
    print("\n⏳ Waiting 15 seconds for WhatsApp Web to load...")
    print("   (Make sure you're logged in!)")
    time.sleep(15)
    
    print("\n" + "=" * 50)
    print("Now showing where automation will click...")
    print("Watch your mouse cursor move to each position!")
    print("=" * 50)
    
    # Position 1: Initial focus click (chat list area)
    focus_x = int(screen_width * 0.2)
    focus_y = int(screen_height * 0.5)
    draw_marker(focus_x, focus_y, "STEP 1: Initial Focus (Chat List Area)")
    
    # Position 2: Search bar click
    search_x = int(screen_width * 0.22)
    search_y = int(screen_height * 0.08)
    draw_marker(search_x, search_y, "STEP 2: Search Bar 'Ask Meta AI or Search'")
    
    # Check if this looks right
    print("\n❓ Is cursor on the search bar? (y/n): ", end="")
    response = input().strip().lower()
    
    if response != 'y':
        print("\n🔧 Let's find the correct position!")
        print("   Move your mouse to the CENTER of the search bar...")
        print("   Press Enter when ready...")
        input()
        
        correct_x, correct_y = pyautogui.position()
        print(f"\n✅ Correct search bar position: ({correct_x}, {correct_y})")
        
        # Calculate percentages
        pct_x = correct_x / screen_width
        pct_y = correct_y / screen_height
        print(f"   As percentage: ({pct_x:.2%} from left, {pct_y:.2%} from top)")
        
        # Update search position
        search_x, search_y = correct_x, correct_y
    
    # Position 3: Message input box
    msg_x = int(screen_width * 0.65)
    msg_y = int(screen_height * 0.93)
    draw_marker(msg_x, msg_y, "STEP 3: Message Input Box (Type a message)")
    
    print("\n❓ Is cursor on the message input box? (y/n): ", end="")
    response = input().strip().lower()
    
    if response != 'y':
        print("\n🔧 Let's find the correct position!")
        print("   Move your mouse to the CENTER of 'Type a message' box...")
        print("   Press Enter when ready...")
        input()
        
        correct_x, correct_y = pyautogui.position()
        print(f"\n✅ Correct message box position: ({correct_x}, {correct_y})")
        
        pct_x = correct_x / screen_width
        pct_y = correct_y / screen_height
        print(f"   As percentage: ({pct_x:.2%} from left, {pct_y:.2%} from top)")
    
    print("\n" + "=" * 50)
    print("DEBUG COMPLETE!")
    print("=" * 50)
    print("\nIf positions were wrong, share the CORRECT percentages")
    print("and I'll update the automation code!")

if __name__ == "__main__":
    main()
